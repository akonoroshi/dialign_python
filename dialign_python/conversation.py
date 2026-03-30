import time
import copy
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
from dialign_python.person import Person


class Conversation:
    def __init__(self, 
                 history: List[tuple[str, str, str]] | None = None, 
                 window: timedelta | int | None = None, 
                 persons: Dict[str, Person] | List[str] | None = None, 
                 exception_tokens: List[str] | None = None, 
                 min_ngram: int = 1, 
                 max_ngram: int | None = None,
                 time_format: str = "%Y-%m-%d %H:%M:%S"
                ):
        """
        Initializes a conversation instance. min_ngram and max_ngram are constraints on the length of n_grams to
        check for.

        Args: history (tuple, optional): a tuple array of timestamps, speakers, and messages within the given window.
        Defaults to an emply list. window (int | timedelta, optional): a number of turns or a range of time to
        consider as the valid conversation history. Defaults to None. persons (dict, optional): a dictionary of all
        the speakers involved in  the conversation. Defaults to an empty dict. exception_tokens (list, optional): an
        array of strings not to include in calculation. Defaults to an empty list. min_ngram (int, optional):
        constraints on the length of n_grams to check for. Defaults to 1. max_ngram (int, optional): constraints on
        the length of n_grams to check for. Defaults to None. time_format (str, optional): format of the timestamp.
        Defaults to "%Y-%m-%d %H:%M:%S".
        """
        if history is None:
            history = []
        if persons is None:
            persons = {}
        if isinstance(persons, list):
            persons = {person: Person(person) for person in persons}
        if exception_tokens is None:
            exception_tokens = []

        self.history = history
        self.length = len(history)
        self.window = window

        # speakers
        self.persons = persons

        # function words seem to be discarded by the tool as non-essential to tracking lexical alignment
        self.exception_tokens = exception_tokens

        # definitions for n_gram lengths, needed for potential optimization of n_gram calculation
        self.min_ngram = min_ngram
        self.max_ngram = max_ngram

        self.time_format = time_format

        # Shared expressions. The key is a expression and the value is a dictionary of the speakers who initiated the
        # expression (initiator) and established the expression (establisher).
        self.shared_expressions = {}

        # output file
        self.output_file = "conversation_output.txt"

        # Cache n-gram generation by effective message/config tuple.
        self._ngram_cache = {}
        # Cache derived artifacts to avoid rebuilding set/counter for repeated history messages.
        self._ngram_artifact_cache = {}
        # Cache parsed timestamps to avoid repeated datetime.strptime on identical strings.
        self._timestamp_cache = {}
        self._timestamp_cache_max_size = 10000

    def _parse_timestamp(self, timestamp: str) -> datetime:
        cached = self._timestamp_cache.get(timestamp)
        if cached is not None:
            return cached

        if len(self._timestamp_cache) >= self._timestamp_cache_max_size:
            oldest_key = next(iter(self._timestamp_cache))
            del self._timestamp_cache[oldest_key]

        parsed = datetime.strptime(timestamp, self.time_format)
        self._timestamp_cache[timestamp] = parsed
        return parsed

    def add_message(self, 
                    speaker: str, 
                    message: str, 
                    timestamp: str | None = None
                    ):
        """
        Add a message to the conversation history and adapt the persons dictionary if there is a new inclusion

        Args:
            speaker (str): the speaker of the message
            message (str): the utterance to be scored
            timestamp (str, optional): the string representation of the timestamp of the message. Defaults to None.
        """

        if speaker not in self.persons:
            self.persons[speaker] = Person(speaker)

        # timestamp is generated each time a message is added:
        if timestamp is None:
            if isinstance(self.window, timedelta):
                raise ValueError("Timestamp is required for time-based window.")
            timestamp = time.strftime(self.time_format)

        # Add the message to the conversation history and remove messages outside the window
        self.history.append((timestamp, speaker, message))
        if self.window is not None:
            if isinstance(self.window, int):
                if len(self.history) > self.window:
                    self.history.pop(0)
            elif isinstance(self.window, timedelta):
                current_time = self._parse_timestamp(timestamp)
                self.history = [(time, speaker, message) for time, speaker, message in self.history if
                                current_time - self._parse_timestamp(time) <= self.window]
        self.length = len(self.history)

    def score_message(self, 
                      speaker: str, 
                      message: str, 
                      timestamp: str | None = None, 
                      add_message_to_history: bool = True, 
                      focus_conversation: List[str] | None = None
                      ) -> tuple[float, float, float, List[str], List[str], List[str]]:
        """
        Function for scoring a message in relation to the conversation.

        Args:
            add_message_to_history:
            speaker (str): the speaker of the message
            message (str): the utterance to be scored
            timestamp (str, optional): the string representation of the timestamp of the message. Defaults to None.
            focus_conversation (List[str], optional): The list of speakers to focus on. Defaults to None.

        Returns:
            tuple: A tuple containing the following elements:
                - der (float): DER score
                - dser (float): DSER score
                - dee (float): DEE score
                - established_expressions (list): List of established expressions
                - repeated_expressions (list): List of self-repeated expressions
                - personal_repetitions (list): List of personal repetitions
        """
        if speaker not in self.persons:
            self.persons[speaker] = Person(speaker)

        if not add_message_to_history:
            saved_shared_expressions = copy.deepcopy(self.shared_expressions)

        if focus_conversation is not None:
            for person in focus_conversation:
                if person not in self.persons:
                    return 0, 0, 0, [], [], []
            der, dser, dee, established_expressions, repeated_expressions, personal_repetitions = self.sub_conversation(focus_conversation, speaker, message)
        else:
            if self.length == 0:
                der, dser, dee = 0, 0, 0
            self.analyze_conversation()
            established_expressions, personal_repetitions, repeated_expressions, _ = self.analyze_message(speaker, message)

            dee = self.calculate_dee(established_expressions, message)
            der, dser = self.create_scores(speaker, message)

        if not add_message_to_history:
            # removing shared expressions from array if the speaker and message are not to be added to conversation
            # history
            self.shared_expressions = saved_shared_expressions
            for n_gram in personal_repetitions:
                self.persons[speaker].remove_repetition(n_gram)
        else:
            self.add_message(speaker, message, timestamp)

        return der, dser, dee, established_expressions, repeated_expressions, personal_repetitions

    def _score_sub_conversation(self, speaker: str, message: str) -> tuple[float, float, float, List[str], List[str], List[str]]:
        if self.length == 0:
            return 0, 0, 0, [], [], []

        print(f'This is the history {self.history}')
        self.analyze_conversation()

        established_expressions, personal_repetitions, repeated_expressions, _ = self.analyze_message(speaker, message)
        dee = self.calculate_dee(established_expressions, message)

        der, dser = self.create_scores(speaker, message)

        return der, dser, dee, established_expressions, repeated_expressions, personal_repetitions

    def sub_conversation(self, focus_conversation: List[str], new_speaker: str, new_message: str) -> tuple[float, float, float, List[str], List[str], List[str]]:
        """
        Creates a sub_conversation for measuring specific interactions between users in a larger conversation. 
        The sub_conversation is deleted following its use.

        Args:
            new_speaker (str): the speaker of the message
            focus_conversation (List[str]): the list of speakers to focus on
            new_message (str): the utterance to be scored

        Returns:
            tuple: A tuple containing the following elements:
                - der (float): DER score
                - dser (float): DSER score
                - dee (float): DEE score
                - established_expressions (list): List of established expressions
                - repeated_expressions (list): List of self-repeated expressions
                - personal_repetitions (list): List of personal repetitions
        """

        sub_history = []

        speakers = {s: self.persons[s] for s in focus_conversation if s in self.persons}
        count = 0
        for timestamp, speaker, past_message in reversed(self.history):
            if speaker in focus_conversation:
                sub_history.append((timestamp, speaker, past_message))
                count += 1
            # if count == self.window:
            #     break
        if count == 1:
            return 0, 0, 0, [], [], []

        if new_speaker in focus_conversation:
            speaker = new_speaker
            message = new_message
        else:
            _, speaker, message = sub_history.pop()

        sub_conversation = Conversation(sub_history, self.window, speakers, self.exception_tokens, self.min_ngram,
                                        self.max_ngram)
        der, dser, dee, established_expressions, repeated_expressions, personal_repetitions = sub_conversation._score_sub_conversation(speaker, message)
        del sub_conversation
        return der, dser, dee, established_expressions, repeated_expressions, personal_repetitions

    def analyze_message(self,
                        current_speaker: str,
                        message: str,
                        sub_window: List[tuple[str, str, str]] | None = None) -> tuple[List[str], List[str], List[str], Dict[str, Dict[str, Any]]]:
        """
        incorporates the message into the conversation sequence and recalculates measurements

        Args:
            current_speaker (str): the speaker of the message
            message (str): the utterance to be scored
            sub_window (list, optional): a windowed conversation history. Defaults to None.

        Returns:
            tuple: A tuple containing the following elements:
                - additions (list): List of newly established shared expressions
                - individual_repetitions (list): List of self-repeated expressions
                - expression_repetitions (list): List of repeated expressions
                - not_shared_expressions (dict): Expressions shared by 2 or more speakers but not shared by all speakers. The key is a expression and the value is a dict that contains the list of the speaker who used the expression and whether it's a free form.
        """

        punctuations = {'.', ',', '!', '?'}

        n_gram_set, current_set, current_counts = self._get_n_gram_artifacts(message)

        if sub_window is None:
            sub_window = self.history

        additions = []
        individual_repetitions = []
        expression_repetitions = set()
        sub_window_len = len(sub_window)

        # Cache past n-grams/counters by message text for this scoring pass.
        per_message_cache = {}
        # Tracks potential shared expressions until all speakers have used the expression.
        pending_shared_expressions = {}
        repetitions = set(self.persons[current_speaker].repetitions)

        for i, turn in enumerate(sub_window):
            timestamp, speaker, past_message = turn[0], turn[1], turn[2]
            cache_key = past_message
            cached = per_message_cache.get(cache_key)
            if cached is None:
                past_n_grams, past_set, past_counts = self._get_n_gram_artifacts(past_message)
                per_message_cache[cache_key] = (past_n_grams, past_set, past_counts)
            else:
                past_n_grams, past_set, past_counts = cached

            matching_n_grams = self._compare_precomputed(
                n_gram_set,
                past_n_grams,
                current_counts,
                past_counts,
                current_set,
                past_set,
            )
            if speaker == current_speaker:
                for n_gram, free_form in matching_n_grams.items():
                    if n_gram not in repetitions and n_gram not in punctuations and free_form:
                        individual_repetitions.append(n_gram)
                        self.persons[current_speaker].add_repetition(n_gram)
                        repetitions.add(n_gram)
            else:
                for n_gram, free_form in matching_n_grams.items():
                    # Keep track of turns where shared expressions are used
                    if n_gram in self.shared_expressions:
                        expression_repetitions.add(n_gram)
                        if i not in self.shared_expressions[n_gram]['turns']:
                            self.shared_expressions[n_gram]['turns'].append(i)
                        if sub_window_len not in self.shared_expressions[n_gram]['turns']:
                            self.shared_expressions[n_gram]['turns'].append(sub_window_len)

                    if n_gram not in self.shared_expressions and n_gram not in punctuations:
                        if n_gram not in pending_shared_expressions:
                            if len(self.persons) == 2:  # not shared expressions are always empty in a two person
                                # conversation
                                if free_form:
                                    additions.append(n_gram)
                                    expression_repetitions.add(n_gram)
                                    self.shared_expressions[n_gram] = {'initiator': speaker,
                                                                       'establisher': current_speaker,
                                                                       'establishmemt turn': sub_window_len,
                                                                       'turns': [i, sub_window_len]}
                            else:
                                pending_shared_expressions[n_gram] = {
                                    'initiator': speaker,
                                    'speakers': {speaker, current_speaker},
                                    'free_form': free_form,
                                }
                        else:
                            pending = pending_shared_expressions[n_gram]
                            pending['free_form'] = pending['free_form'] or free_form
                            pending['speakers'].add(speaker)
                            if len(pending['speakers']) == len(self.persons) and pending['free_form']:
                                additions.append(n_gram)
                                expression_repetitions.add(n_gram)
                                self.shared_expressions[n_gram] = {
                                    'initiator': pending['initiator'],
                                    'establisher': current_speaker, 'establishmemt turn': sub_window_len,
                                    'turns': [i, sub_window_len]}
                                del pending_shared_expressions[n_gram]
        return additions, individual_repetitions, list(expression_repetitions), pending_shared_expressions

    def _compare_precomputed(self,
                             n_gram_set: List[str],
                             past_n_grams: List[str],
                             current_counts: Counter | None = None,
                             past_counts: Counter | None = None,
                             current_set: set[str] | None = None,
                             past_set: set[str] | None = None) -> Dict[str, bool]:
        if current_counts is None:
            current_counts = Counter(n_gram_set)
        if past_counts is None:
            past_counts = Counter(past_n_grams)
        if current_set is None:
            current_set = set(n_gram_set)
        if past_set is None:
            past_set = set(past_n_grams)

        matching_n_grams = list(current_set & past_set)
        free_form = [True] * len(matching_n_grams)

        for i, n_gram in enumerate(matching_n_grams):
            for another_n_gram in matching_n_grams:
                if n_gram == another_n_gram:
                    continue
                if n_gram in another_n_gram:
                    current_n_gram_count = current_counts[n_gram]
                    current_another_n_gram_count = current_counts[another_n_gram]
                    past_n_gram_count = past_counts[n_gram]
                    past_another_n_gram_count = past_counts[another_n_gram]
                    if current_n_gram_count == current_another_n_gram_count and past_n_gram_count == past_another_n_gram_count:
                        free_form[i] = False
                        break

        return {matching_n_gram: free_form[i] for i, matching_n_gram in enumerate(matching_n_grams)}

    def create_scores(self, speaker: str, message: str) -> tuple[float, float]:
        """
        Sets up the respective score calculations for DER and DSER

        Args:
            speaker (str): the speaker of the message
            message (str): the utterance to be scored

        Returns:
            tuple: A tuple containing the following elements:
                - der_score (float): DER score
                - dser_score (float): DSER score
        """
        # message = ''.join([char for char in message if char.isalnum() or char.isspace()])

        if speaker in self.persons:
            person = self.persons[speaker]
            der_score = self.calculate_der(message)
        else:
            print(f"No such person: {speaker}")
            raise NameError

        dser_score = self.calculate_dser(message, person)

        return der_score, dser_score

    def calculate_dee(self, established_expressions: List[str], message: str) -> float:
        """
        Final Step of DEE calculation. Newly established shared expressions.

        Args:
            established_expressions (list): a list of newly established shared expressions
            message (str): the utterance to be scored

        Returns:
            dee (float): DEE score
        """
        # message = ''.join([char for char in message if char.isalnum() or char.isspace()])
        dee = self._fraction_measurement(message, established_expressions, count_once=True)

        return dee

    def calculate_der(self, message: str) -> float:
        """
        Calculate DER measurement final step, speaker shared established expression repetition

        Args:
            message (str): the utterance to be scored

        Returns:
            der (float): DER score
        """
        der = self._fraction_measurement(message, list(self.shared_expressions.keys()))

        return der

    def calculate_dser(self, message: str, speaker: Person) -> float:
        """
        Calculate DSER measurement final step, speaker personal repetition

        Args:
            message (str): the utterance to be scored
            speaker (Person): the speaker of the message

        Returns:
            dser (float): DSER score
        """
        used_tokens = speaker.show_repetitions()
        dser = self._fraction_measurement(message, used_tokens)

        return dser

    def _fraction_measurement(self, message: str, used_tokens: List[str], count_once: bool = False) -> float:
        """
        Measures the amount of a word_set that is comprised of a set of tokens defined by used_tokens and 
        returns the percentage composition.
        """

        word_set = message.split()
        if len(word_set) == 0:
            return 0
        tracking_arr = [0] * len(word_set)

        # Index each token's positions once so each expression only checks viable starts.
        word_positions = {}
        for idx, token in enumerate(word_set):
            if token in word_positions:
                word_positions[token].append(idx)
            else:
                word_positions[token] = [idx]

        # Avoid repeated sorting work if tokens are already in non-increasing n-gram length order.
        needs_sort = False
        for i in range(len(used_tokens) - 1):
            if len(used_tokens[i].split()) < len(used_tokens[i + 1].split()):
                needs_sort = True
                break
        if needs_sort:
            used_tokens.sort(key=lambda x: len(x.split()), reverse=True)

        expression_parts_cache = {}
        for expression in used_tokens:
            if expression not in message:
                continue
            words_in_expression = expression_parts_cache.get(expression)
            if words_in_expression is None:
                words_in_expression = expression.split()
                expression_parts_cache[expression] = words_in_expression

            candidate_positions = word_positions.get(words_in_expression[0], [])
            for i in candidate_positions:
                match = True
                for offset, word_exp in enumerate(words_in_expression):
                    if i + offset >= len(word_set) or word_set[i + offset] != word_exp:
                        match = False
                        break
                if match and tracking_arr[i] == 0:
                    for offset in range(len(words_in_expression)):
                        tracking_arr[i + offset] = 1
                    if count_once:
                        break

        count_ones = tracking_arr.count(1)
        fraction = count_ones / len(tracking_arr)
        return fraction

    def _get_n_gram_artifacts(self, message: str) -> tuple[List[str], set[str], Counter]:
        cache_key = (message, self.min_ngram, self.max_ngram, tuple(self.exception_tokens))
        cached = self._ngram_artifact_cache.get(cache_key)
        if cached is not None:
            return cached

        n_grams = self._create_n_grams(message)
        artifacts = (n_grams, set(n_grams), Counter(n_grams))
        self._ngram_artifact_cache[cache_key] = artifacts
        return artifacts

    def _create_n_grams(self, message: str) -> List[str]:
        """
        Factor a string into a set of n_grams
        """
        try:
            cache_key = (message, self.min_ngram, self.max_ngram, tuple(self.exception_tokens))
            if cache_key in self._ngram_cache:
                return self._ngram_cache[cache_key]

            # message = message.lower()
            # message = ''.join([char for char in message if char.isalnum() or char.isspace()]) # strips punctuation
            # message = message.replace('.', ' .')
            # message = message.replace(',', ' ,')
            words = message.split()
            n_grams = []

            # checking against max_ngram value to apply appropriate constraints
            if self.max_ngram is None:
                maximum = len(words)
            else:
                maximum = self.max_ngram

            # Generate n-grams of size minimum to size maximum (those being variable defined in __init__
            for i in range(len(words)):
                for n in range(self.min_ngram, maximum + 1):
                    if i + n <= len(words):
                        n_gram = ' '.join(words[i:i + n])
                        n_grams.append(n_gram)

            # remove exception tokens
            n_grams_without_exceptions = []
            for h in n_grams:
                if h not in self.exception_tokens:
                    n_grams_without_exceptions.append(h)

            self._ngram_cache[cache_key] = n_grams_without_exceptions
            self._ngram_artifact_cache[cache_key] = (
                n_grams_without_exceptions,
                set(n_grams_without_exceptions),
                Counter(n_grams_without_exceptions),
            )
            return n_grams_without_exceptions
        except ValueError:
            print("Invalid message argument provided to n_gram factoring")
            return []

    def set_n_gram_length_characteristics(self, min_n: int | None = None, max_n: int | None = None):
        """
        Manipulate properties of n_gram for specific calibration

        Args:
            min_n (int, optional): constraints on the length of n_grams to check for. Defaults to None.
            max_n (int, optional): constraints on the length of n_grams to check for. Defaults to None.
        """

        if min_n is not None and isinstance(min_n, int):
            self.min_ngram = min_n
        if max_n is not None and isinstance(max_n, int):
            self.max_ngram = max_n
        self._ngram_cache = {}
        self._ngram_artifact_cache = {}

    def set_window(self, window: int | timedelta):
        """
        Sets a window size of past statements. Only statements in window size are measured. 

        Args: window (int | timedelta): a number of turns or a range of time to consider as the valid conversation
        history. Defaults to None.
        
        Returns: 
            windowed_content (list): a filtered view of the conversation history based on a count or time window.
        """
        if isinstance(window, int):
            # Count-based window: display the last window number of messages
            windowed_content = self.history[-window:] if window > 0 else self.history
            print(f"Windowed Content (last {window} messages):")
        elif isinstance(window, timedelta):
            # Time-based window: filter messages within the window time frame
            current_time = datetime.now()
            windowed_content = []

            # Iterate through each message in self.history and filter based on the time window
            for timestamp, speaker, message in self.history:
                # Convert the timestamp string to a datetime object
                message_time = self._parse_timestamp(timestamp)
                time_difference = current_time - message_time

                # Append to windowed_content only if within the time window
                if time_difference <= window:
                    windowed_content.append((timestamp, speaker, message))

            if not windowed_content:
                print(f"No messages found within the last {window.total_seconds()} seconds.")
            else:
                print(f"Windowed Content (last {window.total_seconds()} seconds):")
        else:
            print("Invalid window type. Use an integer for count or timedelta for time-based window.")
            return

        # Display the filtered windowed content
        for entry in windowed_content:
            print(entry)

        # Return the filtered content without modifying the original history
        return windowed_content

    def except_token(self, token):
        """
        function for excluding a token unnecesary to calculation

        Args:
            token (_type_): _description_
        """
        try:
            if isinstance(token, str):
                self.exception_tokens.append(token)
                self._ngram_cache = {}
                self._ngram_artifact_cache = {}
        except ValueError:
            print("Invalid token argument provided")

    def include_token(self, token):
        """
        function for incorporating a specific token on the exception list

        Args:
            token (_type_): _description_
        """
        try:
            if isinstance(token, str):
                self.exception_tokens.remove(token)
                self._ngram_cache = {}
                self._ngram_artifact_cache = {}
        except ValueError:
            print("Invalid token argument provided")

    def analyze_conversation(self):
        """
        recreate the shared expressions if a windowed history is updated
        """
        if self.window is not None:
            self.shared_expressions = {}
            count = 0
            sub_window = []
            for timestamp, speaker, message in self.history:
                if count > 0:
                    self.analyze_message(speaker, message, sub_window)
                sub_window.append((timestamp, speaker, message))
                count += 1

    def load_conversation_from_file(self, input_file):
        """
        Load a conversation from an input file.

        Args:
            input_file (_type_): _description_
        """
        try:
            with open(input_file, 'r') as file:
                for line in file:
                    parts = line.strip().split(':', 1)
                    if len(parts) == 2:
                        speaker, message = parts
                        self.add_message(speaker.strip(), message.strip())
        except FileNotFoundError:
            print("Invalid input file provided")

    def save_conversation_message_to_file(self, timestamp, speaker, message):
        """
        Save a conversation message to the output file, with a timestamp, speaker, and message.

        Args:
            speaker (_type_): _description_
            message (_type_): _description_
        """
        with open(self.output_file, 'a') as file:
            file.write(f"{timestamp}, $@#, {speaker}, {message}\n")

    def request(self, mode, speaker=None, message=None, add_message_to_history=True, focus_conversation=None):
        """
        Handle all requests to the overall program. @mode is used to 

        Args:
            mode (char): specify the type of operation being done on the dialign. Mode a is adding which takes
        speaker and the message and adds them. The score mode does a similar thing but if scoring condition is set to
        1 the message is added to conversation history. The mode n is used to set n_gram characteristics and in this
        case speaker and message are numbers (not strings as for add_message and score_message) that limit the N-gram
        creation. window size only takes one argument after its mode(w) which is a number refering to the amount of
        past conversations to take into account. e and i are used to excerpt and include specific words or exclude
        them. These are entered in the form of a list of the strings to be excluded and included.

            speaker (str): _description_ Defaults to None.

            message (_type_, optional): _description_. Defaults to None.

            add_message_to_history (bool, optional): _description_. Defaults to True.
            
            focus_conversation (_type_, optional): _description_. Defaults to None.

        * In the case of certain modes such as 'w', speaker and message may contain integer values. 
        """
        # add
        if mode == 'a':
            try:
                self.add_message(speaker, message)
            except ValueError:
                print("Error adding message.")
        # score
        elif mode == 's':
            try:
                # focus_conversation = ['bob', 'tim']
                if self.length == 0:
                    return 0, 0, 0

                if focus_conversation is None:
                    der, dser, dee, _, _, _ = self.score_message(speaker, message,
                                                                 add_message_to_history=add_message_to_history)
                else:
                    der, dser, dee, _, _, _ = self.score_message(speaker, message,
                                                                 focus_conversation=focus_conversation,
                                                                 add_message_to_history=add_message_to_history)
                print(f'Shared Expressions : {self.shared_expressions}')
                print(f'DER: {der}')
                print(f'DSER: {dser}')
                print(f'DEE: {dee}')
                return der, dser, dee
            except ValueError:
                print("Error scoring message.")
        # set n_gram characteristics
        elif mode == 'n':
            try:
                # in this case the speaker and message would be numbers which limit the window size
                self.set_n_gram_length_characteristics(speaker, message)
                print(f'N_gram maximum : {self.max_ngram}')
                print(self.min_ngram)
            except ValueError:
                print("Error adjusting N-gram length characteristics.")
        # set window size
        elif mode == 'w':
            try:
                if speaker.isdigit():
                    # Count-based window
                    count_window = int(speaker)
                    windowed_history = self.set_window(count_window)
                else:
                    # Time-based window in seconds
                    try:
                        seconds = int(message)
                        time_window = timedelta(seconds=seconds)
                        windowed_history = self.set_window(time_window)
                    except ValueError:
                        print("Invalid time window format. Please enter seconds as an integer.")
            except ValueError:
                print("Invalid window type provided.")
        # except token
        elif mode == 'e':
            try:
                # in this case the speaker paramter should be an array of values to except
                for token in speaker:
                    self.except_token(token)
            except ValueError:
                print("Error excepting specific tokens")
        # include token
        elif mode == 'i':
            try:
                # in this case the speaker parameter should be an array of values to inclusion
                for token in speaker:
                    self.include_token(token)
            except ValueError:
                print("Error including specific tokens.")

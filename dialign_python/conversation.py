import time
import copy
from datetime import datetime, timedelta
from person import Person
from Parallel_score import score_utterances_in_parallel

class Conversation:
    def __init__(self, history=None, window=None, persons=None, exception_tokens=None, min_ngram=1, max_ngram=None, time_format="%Y-%m-%d %H:%M:%S"):
        """
        Initializes a conversation instance. min_ngram and max_ngram are constraints on the length of n_grams to check for. 

        Args:
            history (tuple, optional): a tuple array of timestamps, speakers, and messages within the given window. Defaults to an emply list.
            window (int | timedelta, optional): a number of turns or a range of time to consider as the valid conversation history. Defaults to None.
            persons (dict, optional): a dictionary of all the speakers involved in  the conversation. Defaults to an empty dict.
            exception_tokens (list, optional): an array of strings not to include in calculation. Defaults to an empty list.
            min_ngram (int, optional): constraints on the length of n_grams to check for. Defaults to 1.
            max_ngram (int, optional): constraints on the length of n_grams to check for. Defaults to None.
            time_format (str, optional): format of the timestamp. Defaults to "%Y-%m-%d %H:%M:%S".
        """
        if history is None:
            history = []
        if persons is None:
            persons = {}
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
        
        # Shared expressions. The key is a expression and the value is a dictionary of the speakers who initiated the expression (initiator) and established the expression (establisher).
        self.shared_expressions = {}

        # output file
        self.output_file = "conversation_output.txt"

    def parallel_score(self, utterances, speaker, add_message_to_history):
        """
        parallel scoring to the external module.

        Args:
            utterances (list): list of utterances to score
            speaker (str): speaker of the utterances
            add_message_to_history (bool): whether to add the utterances to the conversation history
        
        Returns:
            list: list of tuples containing the utterance and the dictionary of scores
        """
        try:
            results = score_utterances_in_parallel(self, utterances, speaker, add_message_to_history)
        except Exception as e:
            print(f"Error in parallel scoring: {e}")
            results = None
        return results
    
    def add_message(self, speaker, message, timestamp=None):
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
                self.history = [(time, speaker, message) for time, speaker, message in self.history if datetime.strptime(timestamp, self.time_format) - datetime.strptime(time, self.time_format) <= self.window]
        self.length = len(self.history)

    def score_message(self, speaker, message, timestamp=None, add_message_to_history=True, focus_conversation=None):
        """
        Function for scoring a message in relation to the conversation.

        Args:
            speaker (str): the speaker of the message
            message (str): the utterance to be scored
            timestamp (str, optional): the string representation of the timestamp of the message. Defaults to None.
            focus_conversation (_type_, optional): _description_. Defaults to None.

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
            der, dser, dee = self.sub_conversation(focus_conversation, speaker, message)
        else:
            if self.length == 0:
                der, dser, dee = 0, 0, 0
            self.analyze_conversation()
            established_expressions, personal_repetitions, repeated_expressions = self.analyze_message(speaker, message)
            
            dee = self.calculate_dee(established_expressions, message)
            der, dser = self.create_scores(speaker, message)

        if not add_message_to_history:
            # removing shared expressions from array if the speaker and message are not to be added to conversastion history
            self.shared_expressions = saved_shared_expressions
            for n_gram in personal_repetitions:
                self.persons[speaker].remove_repetition(n_gram)
        else:
            self.add_message(speaker, message, timestamp)
            
        return der, dser, dee, established_expressions, repeated_expressions, personal_repetitions


    def _score_sub_conversation(self, speaker, message, focus_conversation=None):
        if self.length == 0:
            return 0, 0, 0
        
        print (f'This is the history {self.history}')
        self.analyze_conversation()

        established_expressions, personal_repetitions, _ = self.analyze_message(speaker, message)
        dee = self.calculate_dee(established_expressions, message)

        der, dser = self.create_scores(speaker, message)

        return der, dser, dee

    
    def sub_conversation(self, focus_conversation, new_speaker, new_message):
        """
        Creates a sub_conversation for measuring specific interactions between users in a larger conversation. 
        The sub_conversation is deleted following its use.

        Args:
            focus_conversation (_type_): _description_
            speaker (str): the speaker of the message
            message (str): the utterance to be scored

        Returns:
            _type_: _description_
        """
        
    
        reverse_history = self.history
        reverse_history.reverse()
        sub_history = []

        speakers = {s: self.persons[s] for s in focus_conversation if s in self.persons}
        count = 0
        for speaker, past_message in self.history:
            if speaker in focus_conversation:
                sub_history.append((speaker, past_message))
                count += 1
            # if count == self.window:
            #     break
        if count == 1:
            return 0,0,0

        if new_speaker in focus_conversation:
            speaker = new_speaker
            message = new_message
        else:
            speaker, message = sub_history.pop()
        
        sub_conversation = Conversation(sub_history, self.window, speakers, self.exception_tokens, self.min_ngram, self.max_ngram)
        a, b, c = sub_conversation._score_sub_conversation(speaker, message)
        del sub_conversation
        return a, b, c


    def analyze_message(self, current_speaker, message, sub_window = None):
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
        """

        punctuations = ['.', ',', '!', '?']

        n_gram_set = self._create_n_grams(message)

        if sub_window is None:
            sub_window = self.history

        additions = []
        individual_repetitions = []
        expression_repetitions = set()
        # Expressions shared by 2 or more speakers but not shared by all speakers. The key is a expression and the value is a list of the speaker who used the expression.
        not_shared_expressions = {}

        for i, turn in enumerate(sub_window):
            timestamp, speaker, past_message = turn[0], turn[1], turn[2]
            if speaker == current_speaker:
                matching_n_grams = self._compare(past_message, n_gram_set)
                repetitions = set(self.persons[current_speaker].repetitions)
                for n_gram, free_form in matching_n_grams.items():
                    if n_gram not in repetitions and n_gram not in punctuations and free_form:
                        individual_repetitions.append(n_gram)
                        self.persons[current_speaker].add_repetition(n_gram)
            else:
                matching_n_grams = self._compare(past_message, n_gram_set)
                for n_gram, free_form in matching_n_grams.items():
                    # Keep track of turns where shared expressions are used
                    if n_gram in self.shared_expressions:
                        expression_repetitions.add(n_gram)
                        if i not in self.shared_expressions[n_gram]['turns']:
                            self.shared_expressions[n_gram]['turns'].append(i)
                        if len(sub_window) not in self.shared_expressions[n_gram]['turns']:
                            self.shared_expressions[n_gram]['turns'].append(len(sub_window))
                    
                    if n_gram not in self.shared_expressions and n_gram not in punctuations:
                        if n_gram not in not_shared_expressions: # New not shared expression is found
                            if len(self.persons) == 2: # not shared expressions are always empty in a two person conversation
                                if free_form:
                                    additions.append(n_gram)
                                    expression_repetitions.add(n_gram)
                                    self.shared_expressions[n_gram] = {'initiator': speaker, 'establisher': current_speaker, 'establishmemt turn': len(sub_window), 'turns': [i, len(sub_window)]}
                            else:
                                not_shared_expressions[n_gram] = {'speakers': [speaker, current_speaker], 'free_form': free_form}
                        else: # There is at least one speaker other than current_speaker who have used this expression
                            not_shared_expressions[n_gram]['free_form'] = not_shared_expressions[n_gram]['free_form'] or free_form
                            if speaker not in not_shared_expressions[n_gram]['speakers']:
                                not_shared_expressions[n_gram]['speakers'].append(speaker)
                            if len(not_shared_expressions[n_gram]['speakers']) == len(self.persons) and not_shared_expressions[n_gram]['free_form']:
                                additions.append(n_gram)
                                expression_repetitions.add(n_gram)
                                self.shared_expressions[n_gram] = {'initiator': not_shared_expressions[n_gram]['speakers'][0], 'establisher': current_speaker, 'establishmemt turn': len(sub_window), 'turns': [i, len(sub_window)]}
                                del not_shared_expressions[n_gram]
        return additions, individual_repetitions, list(expression_repetitions)
    

    def create_scores(self, speaker, message):
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
        #message = ''.join([char for char in message if char.isalnum() or char.isspace()])
        
        if speaker in self.persons:
            person = self.persons[speaker]
            der_score = self.calculate_der(message)
        else:
            print(f"No such person: {speaker}")
            return NameError

        dser_score = self.calculate_dser(message, person)

        return der_score, dser_score

    def calculate_dee(self, established_expressions, message):
        """
        Final Step of DEE calculation. Newly established shared expressions.

        Args:
            established_expressions (list): a list of newly established shared expressions
            message (str): the utterance to be scored

        Returns:
            dee (float): DEE score
        """
        #message = ''.join([char for char in message if char.isalnum() or char.isspace()])
        dee = self._fraction_measurement(message, established_expressions, count_once=True)

        return dee

    def calculate_der(self, message):
        """
        Calculate DER measurement final step, speaker shared established expression repetition

        Args:
            message (str): the utterance to be scored

        Returns:
            der (float): DER score
        """
        der = self._fraction_measurement(message, list(self.shared_expressions.keys()))

        return der
    
    def calculate_dser(self, message, speaker):
        """
        Calculate DSER measurement final step, speaker personal repetition

        Args:
            message (str): the utterance to be scored
            speaker (str): the speaker of the message

        Returns:
            dser (float): DSER score
        """
        used_tokens = speaker.show_repetitions()
        dser = self._fraction_measurement(message, used_tokens)

        return dser

    def _fraction_measurement(self, message, used_tokens, count_once=False):
        """
        Measures the amount of a word_set that is comprised of a set of tokens defined by used_tokens and 
        returns the percentage composition.
        """
        
        word_set = message.split()
        if len(word_set) == 0:
            return 0
        tracking_arr = [0] * len(word_set)
        used_tokens.sort(key=lambda x: len(x.split()), reverse=True)
        
        for expression in used_tokens:
            if expression in message:
                words_in_expression = expression.split()
                for i, word in enumerate(word_set):
                    if word == words_in_expression[0]:
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
        fraction = count_ones/len(tracking_arr)
        return fraction
    
    def _compare(self, message, n_gram_set):
        """
        Compares a message with an n_gram set
        """
        try:
            past_n_grams = self._create_n_grams(message)
            matching_n_grams = list(set([n_gram for n_gram in n_gram_set if n_gram in past_n_grams]))
            free_form = [True] * len(matching_n_grams)
            for i, n_gram in enumerate(matching_n_grams):
                for j, another_n_gram in enumerate(matching_n_grams):
                    if n_gram == another_n_gram:
                        continue
                    if n_gram in another_n_gram:
                        current_n_gram_count = n_gram_set.count(n_gram)
                        current_another_n_gram_count = n_gram_set.count(another_n_gram)
                        past_n_gram_count = past_n_grams.count(n_gram)
                        past_another_n_gram_count = past_n_grams.count(another_n_gram)
                        if current_n_gram_count == current_another_n_gram_count and past_n_gram_count == past_another_n_gram_count:
                            free_form[i] = False
                            break
            return {matching_n_gram: free_form[i] for i, matching_n_gram in enumerate(matching_n_grams)}
        except: 
            print ("Error in comparing current to past n-grams")


    def _create_n_grams(self, message):
        """
        Factor a string into a set of n_grams
        """
        try:
            # message = message.lower()
            # message = ''.join([char for char in message if char.isalnum() or char.isspace()]) # strips punctuation
            # message = message.replace('.', ' .')
            # message = message.replace(',', ' ,')
            words = message.split()
            n_grams = []
            
            # checking against max_ngram value to apply appropriate constraints
            if self.max_ngram == None:
                maximum = len(words)
            else:
                maximum = self.max_ngram

            # Generate n-grams of size minimum to size maximum (those being variable defined in __init__
            for i in range(len(words)):
                for n in range(self.min_ngram, maximum + 1):
                    if i + n <= len(words):
                        n_gram = ' '.join(words[i:i+n])
                        n_grams.append(n_gram)
            
            # remove exception tokens
            n_grams_without_exceptions = []
            for h in n_grams:
                if h not in self.exception_tokens:
                    n_grams_without_exceptions.append(h)

            return n_grams_without_exceptions
        except ValueError:
            print ("Invalid message argument provided to n_gram factoring")

    def set_n_gram_length_characteristics(self, min_n=None, max_n=None):
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

    def set_window(self, window):
        """
        Sets a window size of past statements. Only statements in window size are measured. 

        Args:
            window (int | timedelta): a number of turns or a range of time to consider as the valid conversation history. Defaults to None.
        
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
                message_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
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
        except ValueError:
            print ("Invalid token argument provided")
    
    
    def include_token(self, token):
        """
        function for incorporating a specific token on the exception list

        Args:
            token (_type_): _description_
        """
        try:
            if isinstance(token, str):
                self.exception_tokens.remove(token)
        except ValueError:
            print ("Invalid token argument provided")
    

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
            print ("Invalid input file provided")

    def save_conversation_message_to_file(self, timestamp, speaker, message):
        """
        Save a conversation message to the output file, with a timestamp, speaker, and message.

        Args:
            speaker (_type_): _description_
            message (_type_): _description_
        """
        with open(self.output_file, 'a') as file:
            file.write(f"{timestamp}, $@#, {speaker}, {message}\n")


    def request(self, mode,  speaker=None, message=None, add_message_to_history=True, focus_conversation=None, utterances_to_score=None):
        """
        Handle all requests to the overall program. @mode is used to 

        Args:
            mode (char): specify the type of operation being done on the dialign. Mode a is adding which takes speaker and the message and adds them. The score mode does a similar thing but if scoring condition is set to 1 the message is added to conversation history. The mode n is used to set n_gram characteristics and in this case speaker and message are numbers (not strings as for add_message and score_message) that limit the N-gram creation. window size only takes one argument after its mode(w) which is a number refering to the amount of past conversations to take into account. e and i are used to excerpt and include specific words or exclude them. These are entered in the form of a list of the strings to be excluded and included. 
            speaker (str): _description_ Defaults to None.
            message (_type_, optional): _description_. Defaults to None.
            add_message_to_history (bool, optional): _description_. Defaults to True.
            focus_conversation (_type_, optional): _description_. Defaults to None.
            utterances_to_score (list, optional): utterances to score in parallel. Defaults to None.

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
                #focus_conversation = ['bob', 'tim']
                if self.length == 0:
                    return 0,0,0
                
                if focus_conversation is None:
                    der, dser, dee, _, _, _ = self.score_message(speaker, message, add_message_to_history=add_message_to_history)
                else:
                    der, dser, dee, _, _, _ = self.score_message(speaker, message, focus_conversation=focus_conversation, add_message_to_history=add_message_to_history)
                print (f'Shared Expressions : {self.shared_expressions}')
                print (f'DER: {der}')
                print (f'DSER: {dser}')
                print (f'DEE: {dee}')
                return der, dser, dee
            except ValueError:
                print("Error scoring message.")
        #set n_gram characteristics
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
            else:
                print("No results from parallel scoring.")
        elif mode == 'p':
            results = self.parallel_score(utterances_to_score, "BatchSpeaker", False)
            if results:
                print("\nParallel Scoring Results:")
                for utterance, scores in results:
                    if scores and isinstance(scores, dict):
                        der = scores.get("DER", "N/A")
                        dser = scores.get("DSER", "N/A")
                        dee = scores.get("DEE", "N/A")
                        print(f"Utterance: {utterance}\nDER: {der}\nDSER: {dser}\nDEE: {dee}\n")
                    else:
                        print(f"Utterance: {utterance}\nScoring Failed.\n")
            else:
                print("No results from parallel scoring.")
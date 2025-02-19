import time
import copy
import re
from collections import Counter
import pprint
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import spacy
from scipy.stats import entropy
from .person import Person

nlp = spacy.load("en_core_web_sm")

class Conversation:
    def __init__(self, history=None, window=None, persons=None, exception_tokens=None, min_ngram=1, max_ngram=None, suppress_debug=False):
        """
        Initializes a conversation instance. min_ngram and max_ngram are constraints on the length of n_grams to check for. 

        Args:
            history (tuple, optional): a tuple array of timestamps, speakers, and messages within the given window. Defaults to an emply list.
            window (int | timedelta, optional): a number referring to the window size. Defaults to None.
            persons (dict, optional): a dictionary of all the speakers involved in  the conversation. Defaults to an empty dict.
            exception_tokens (list, optional): an array of strings not to include in calculation. Defaults to an empty list.
            min_ngram (int, optional): constraints on the length of n_grams to check for. Defaults to 1.
            max_ngram (_type_, optional): constraints on the length of n_grams to check for. Defaults to None.
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
        
        # Shared expressions. The key is a expression and the value is a dictionary of the speakers who initiated the expression (initiator) and established the expression (establisher).
        self.shared_expressions = {}

        # output file
        self.output_file = "conversation_output.txt"

        self.suppress_debug = suppress_debug  # Debug suppression flag

    def add_message(self, speaker, message, timestamp=None):
        """
        Add a message to the conversation history and adapt the persons dictionary if there is a new inclusion

        Args:
            speaker (_type_): _description_
            message (_type_): _description_
        """

        if speaker not in self.persons:
            self.persons[speaker] = Person(speaker)

        # timestamp is generated each time a message is added:
        if timestamp is None:
            if isinstance(self.window, timedelta):
                raise ValueError("Timestamp is required for time-based window.")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Add the message to the conversation history and remove messages outside the window
        self.history.append((timestamp, speaker, message))
        if self.window is not None:
            if isinstance(self.window, int):
                if len(self.history) > self.window:
                    self.history.pop(0)
            elif isinstance(self.window, timedelta):
                time_format = "%H:%M:%S.%f"
                self.history = [(time, speaker, message) for time, speaker, message in self.history if datetime.strptime(timestamp, time_format) - datetime.strptime(time, time_format) <= self.window]
        self.length = len(self.history)

    def score_message(self, speaker, message, timestamp=None, add_message=True, focus_conversation=None): 
        """
        Function for scoring a message in relation to the conversation.

        Args:
            speaker (_type_): _description_
            message (_type_): _description_
            focus_conversation (_type_, optional): _description_. Defaults to None.

        Raises:
            NameError: _description_

        Returns:
            _type_: _description_
        """
        if speaker not in self.persons:
            self.persons[speaker] = Person(speaker)
        
        if not add_message:
            saved_shared_expressions = copy.deepcopy(self.shared_expressions)

        if focus_conversation is not None:
            for person in focus_conversation:
                if person not in self.persons:
                    return 0, 0, 0, [], []
            der, dser, dee = self.sub_conversation(focus_conversation, speaker, message)
        else:
            if self.length == 0:
                der, dser, dee = 0, 0, 0
            self.analyze_conversation()
            established_expressions, personal_repetitions, repeated_expressions = self.analyze_message(speaker, message)
            
            dee = self.calculate_dee(established_expressions, message)
            der, dser = self.create_scores(speaker, message)

        if not add_message:
            # removing shared expressions from array if the speaker and message are not to be added to conversastion history
            self.shared_expressions = saved_shared_expressions
            for n_gram in personal_repetitions:
                self.persons[speaker].remove_repetition(n_gram)
        else:
            self.add_message(speaker, message, timestamp)
            
        return der, dser, dee, established_expressions, repeated_expressions


    def score_sub_conversation(self, speaker, message, scoring_condition, focus_conversation=None):
        """
        Scoring for sub_conversation. Strips extra functionality not needed for a sub_conversation measurement.

        Args:
            speaker (_type_): _description_
            message (_type_): _description_
            scoring_condition (_type_): _description_
            focus_conversation (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
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
            speaker (_type_): _description_
            message (_type_): _description_

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
        a, b, c = sub_conversation.score_sub_conversation(speaker, message, 0)
        del sub_conversation
        return a, b, c


    def analyze_message(self, current_speaker, message, sub_window = None):
        """
        incorporates the message into the conversation sequence and recalculates measurements

        Args:
            current_speaker (_type_): _description_
            message (_type_): _description_

        Returns:
            _type_: _description_
        """

        punctuations = ['.', ',', '!', '?']

        n_gram_set = self.create_n_grams(message)

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
                matching_n_grams = self.compare(past_message, n_gram_set)
                repetitions = set(self.persons[current_speaker].repetitions)
                for n_gram in matching_n_grams.keys():
                    if n_gram not in repetitions:
                        individual_repetitions.append(n_gram)
                        self.persons[current_speaker].add_repetition(n_gram)
            else:
                matching_n_grams = self.compare(past_message, n_gram_set)
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
            speaker (_type_): _description_
            message (_type_): _description_

        Returns:
            _type_: _description_
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
            established_expressions (_type_): _description_
            message (_type_): _description_

        Returns:
            _type_: _description_
        """
        #message = ''.join([char for char in message if char.isalnum() or char.isspace()])
        dee = self.fraction_measurement(message, established_expressions, count_once=True)

        return dee


    def calculate_der(self, message):
        """
        Calculate DER measurement final step, speaker shared established expression repetition

        Args:
            word_set (_type_): _description_

        Returns:
            _type_: _description_
        """
        der = self.fraction_measurement(message, list(self.shared_expressions.keys()))

        return der
    
    def calculate_dser(self, message, speaker):
        """
        Calculate DSER measurement final step, speaker personal repetition

        Args:
            word_set (_type_): _description_
            speaker (_type_): _description_

        Returns:
            _type_: _description_
        """
        used_tokens = speaker.show_repetitions()
        dser = self.fraction_measurement(message, used_tokens)

        return dser

    def fraction_measurement(self, message, used_tokens, count_once=False):
        """
        Measures the amount of a word_set that is comprised of a set of tokens defined by used_tokens and 
        returns the percentage composition.

        Args:
            word_set (_type_): _description_
            used_tokens (_type_): _description_

        Returns:
            _type_: _description_
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
    
    def compare(self, message, n_gram_set):
        """
        # compares a message with an n_gram set

        Args:
            message (_type_): _description_
            n_gram_set (_type_): _description_

        Returns:
            _type_: _description_
        """
        try:
            past_n_grams = self.create_n_grams(message)
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


    def create_n_grams(self, message):
        """
        Factor a string into a set of n_grams

        Args:
            message (_type_): _description_

        Returns:
            _type_: _description_
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
        manipulate properties of n_gram for specific calibration

        Args:
            min_n (_type_, optional): _description_. Defaults to None.
            max_n (_type_, optional): _description_. Defaults to None.
        """

        if min_n is not None and isinstance(min_n, int):
            self.min_ngram = min_n
        if max_n is not None and isinstance(max_n, int):
            self.max_ngram = max_n
    
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

        if not self.suppress_debug:  # Check debug suppression flag
            print(self.shared_expressions)


    def request(self, mode,  speaker, message=None, scoring_condition=0, focus_conversation=None, uttrerance_to_score=None):
        """
        this function handles all requests to the overall program. @mode is used to specify the type of operation being done on the dialign. Mode a is adding which takes 
        speaker and the message and adds them. The score mode does a similar thing but if scoring condition is set to 1 the message is added to conversation history. The mode
        n is used to set n_gram characteristics and in this case speaker and message are numbers (not strings as for add_message and score_message) that limit the N-gram creation.
        window size only takes one argument after its mode(w) which is a number refering to the amount of past conversations to take into account. e and i are used to excerpt and 
        include specific words or exclude them. These are entered in the form of a list of the strings to be excluded and included. 

        Args:
            mode (_type_): _description_
            speaker (_type_): _description_
            message (_type_, optional): _description_. Defaults to None.
            scoring_condition (int, optional): _description_. Defaults to 0.
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
                #focus_conversation = ['bob', 'tim']
                if self.length == 0:
                    return 0,0,0
                
                if focus_conversation is None:
                    der, dser, dee, _, _ = self.score_message(speaker, message)
                else:
                    der, dser, dee, _, _ = self.score_message(speaker, message, focus_conversation=focus_conversation)
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


def read_transcript(input_file: str, speaker_col: str, message_col: str, sheet_name=None, valid_speakers=None, filters=None):
    if input_file.endswith('.xlsx'):
        if sheet_name is None:
            df = pd.read_excel(input_file)
        else:
            df = pd.read_excel(input_file, sheet_name=sheet_name)
    elif input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        raise ValueError("Invalid input file format. Please provide a .xlsx or .csv file.")
    df[speaker_col] = df[speaker_col].str.replace(':', '')
    df[message_col] = df[message_col].str.replace(r'\\[.+\\]', '', regex=True)
    if valid_speakers is not None:
        df = df[df[speaker_col].isin(valid_speakers)]
    if filters is not None:
        for col, vals in filters.items():
            df = df[df[col].isin(vals)]
    return df.dropna(subset=[speaker_col]).reset_index(drop=True)

def dialign(input_file: str, speaker_col: str, message_col: str, timestamp_col=None, valid_speakers=None, sheet_name=None, filters=None, window=None, exception_tokens=None, min_ngram=1, max_ngram=None, suppress_debug=False):
    """
    Function to run the Dialign algorithm on a conversation dataset.

    Args:
        df (str): pandas DataFrame containing the conversation data.
        speaker_col (str): Name of the column containing the speaker data.
        message_col (str): Name of the column containing the message data.
        timestamp_col (str, optional): Name of the column containing the timestamp data. Defaults to None.
        valid_speakers (list, optional): List of valid speakers to include in the analysis. Defaults to None.
        window (int | timedelta, optional): Count or time window for the conversation history. Defaults to None.
        exception_tokens (list, optional): List of tokens to exclude from the analysis. Defaults to None.
        min_ngram (int, optional): Minimum n-gram length for the analysis. Defaults to 1.
        max_ngram (int, optional): Maximum n-gram length for the analysis. Defaults to None.
        suppress_debug (bool, optional): Flag to suppress debug output. Defaults to False.

    Returns:
        speaker_independent (dict): Dictionary containing the speaker-independent scores (ER, SER, EE, Total tokens,
        Num. shared expressions) for the conversation.
        speaker_dependent (dict): Dictionary containing the speaker-dependent scores (ER, SER, EE, Total tokens,
        Initiated, Established) for each `valud_speaker` for the conversation.
    """

    df = read_transcript(input_file, speaker_col, message_col, sheet_name, valid_speakers, filters)

    # Initialize the conversation instance
    if valid_speakers is not None:
        persons = {speaker: Person(speaker) for speaker in valid_speakers}
    else:
        persons = {speaker: Person(speaker) for speaker in df[speaker_col].unique()}
    conversation = Conversation(persons=persons, window=window, exception_tokens=exception_tokens, min_ngram=min_ngram, max_ngram=max_ngram, suppress_debug=suppress_debug)

    # Iterate through each row in the conversation data
    repetition_num = 0
    self_repetition_num = 0
    establishment_num = 0
    total_tokens = 0
    speaker_dependent = {speaker: {"ER": 0, "SER": 0, "EE": 0, "Total tokens": 0, "Initiated": 0, "Established": 0} for speaker in valid_speakers}
    online_metrics = []
    for _, row in df.iterrows():
        speaker = row[speaker_col]
        doc = nlp(re.sub(r'\[.*\]', '', row[message_col]).replace('_', ''))
        tokens = [token.text for token in doc]
        message = ' '.join(tokens).lower()
        if timestamp_col is not None:
            timestamp = row[timestamp_col]
            der, dser, dee, established_expression, repeated_expression = conversation.score_message(speaker, message, timestamp, add_message=True)
        else:
            der, dser, dee, established_expression, repeated_expression = conversation.score_message(speaker, message, add_message=True)
        speaker_dependent[speaker]["ER"] += round(der * len(tokens))
        speaker_dependent[speaker]["SER"] += round(dser * len(tokens))
        speaker_dependent[speaker]["EE"] += round(dee * len(tokens))
        speaker_dependent[speaker]["Total tokens"] += len(tokens)
        repetition_num += round(der * len(tokens))
        self_repetition_num += round(dser * len(tokens))
        establishment_num += round(dee * len(tokens))
        total_tokens += len(tokens)
        online_metrics.append({'Speaker': speaker, 'Message': message, 'DER': der, 'DSER': dser, 'DEE': dee, 'Established Expression': established_expression, 'Repeated Expression': repeated_expression})
    
    # Compute the final speaker-dependent scores
    for speaker in valid_speakers:
        if speaker_dependent[speaker]["Total tokens"] > 0:
            speaker_dependent[speaker]["ER"] /= speaker_dependent[speaker]["Total tokens"]
            speaker_dependent[speaker]["SER"] /= speaker_dependent[speaker]["Total tokens"]
            speaker_dependent[speaker]["EE"] /= speaker_dependent[speaker]["Total tokens"]
        else:
            speaker_dependent[speaker]["ER"] = 0
            speaker_dependent[speaker]["SER"] = 0
            speaker_dependent[speaker]["EE"] = 0
    for data in conversation.shared_expressions.values():
        speaker_dependent[data['initiator']]["Initiated"] += 1 / len(conversation.shared_expressions)
        speaker_dependent[data['establisher']]["Established"] += 1 / len(conversation.shared_expressions)
    
    # Compute the final speaker-independent scores
    if total_tokens > 0:
        speaker_independent = {
            "ER": repetition_num / total_tokens,
            "SER": self_repetition_num / total_tokens,
            "EE": establishment_num / total_tokens
        }
    else:
        speaker_independent = {
            "ER": 0,
            "SER": 0,
            "EE": 0
        }
    speaker_independent["Total tokens"] = total_tokens
    speaker_independent["Num. shared expressions"] = len(conversation.shared_expressions)
    speaker_independent['EV'] = len(conversation.shared_expressions) / total_tokens
    expression_lengths = [len(expression.split()) for expression in conversation.shared_expressions]
    counter = Counter(expression_lengths)
    _, counts = zip(*counter.items())
    probabilities = np.array(counts) / len(expression_lengths)
    speaker_independent['ENTR'] = float(entropy(probabilities))
    speaker_independent['L'] = float(np.mean(expression_lengths))
    speaker_independent['LMAX'] = int(np.max(expression_lengths))
    self_repetitions = {speaker: person.show_repetitions() for speaker, person in conversation.persons.items()}
        
    return speaker_independent, speaker_dependent, conversation.shared_expressions, self_repetitions, online_metrics

if __name__ == "__main__":
    # Example usage of the dialign function
    input_file = "../../pilot_data/Deidentified-Transcripts/Dyad/with_receivers_base_time_annotated.xlsx"
    speaker_col = "Speaker"
    message_col = "Modified (English)"
    timestamp_col = "Start Time"
    valid_speakers = ["Emma", "1_a", "1_b"]
    sheet_name = "1ab"
    filters = {"On-Task/Off-Task": ["on-task"], 'Receiver': valid_speakers}
    speaker_independent, speaker_dependent, shared_expressions, self_repetitions, online_metrics = dialign(input_file, speaker_col, message_col, timestamp_col, valid_speakers, sheet_name, filters, suppress_debug=True)
    print(f"Speaker independent: {speaker_independent}")
    print("Speaker dependent:")
    for speaker, data in speaker_dependent.items():
        print(f"{speaker}: {data}")
    pprint.pprint(f"Shared expressions: {shared_expressions}")
    #pprint.pprint(online_metrics)
    # print("Self repetitions:")
    # for speaker, data in self_repetitions.items():
    #     print(f"{speaker}: {data}")

    # message = 'so i can multiply two over three by three over two . what do i do next ?'
    # conversation = Conversation()
    # n_gram_set = conversation.create_n_grams(message)
    # past_message = "you 're going to multiply one over twenty by three over two ."
    # print(conversation.compare(past_message, n_gram_set))
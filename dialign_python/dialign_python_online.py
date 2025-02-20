import time
from datetime import datetime, timedelta
from Parallel_score import score_utterances_in_parallel
from person import Person

class Conversation:
    def __init__(self, history=None, length=None, window=None, persons=None, exception_tokens=None, min_ngram=None, max_ngram=None, suppress_debug=False):
        """
        Initializes a conversation instance. History is a tuple array of all speakers and messages, length is the length
        of history, window is a number referring to the window size, persons is a dictionary of all the speakers involved in 
        the conversation, exception_tokens is an array of strings not to include in calculation, and min_ngram and max_ngram are constraints
        on the length of n_grams to check for. 

        Args:
            history (_type_, optional): _description_. Defaults to None.
            length (_type_, optional): _description_. Defaults to None.
            window (_type_, optional): _description_. Defaults to None.
            persons (_type_, optional): _description_. Defaults to None.
            exception_tokens (_type_, optional): _description_. Defaults to None.
            min_ngram (_type_, optional): _description_. Defaults to None.
            max_ngram (_type_, optional): _description_. Defaults to None.
        """
        if history != None:
            self.history = history
            self.length = length
            self.window = window
            self.persons = persons
            self.exception_tokens = exception_tokens
            self.min_ngram = min_ngram
            self.max_ngram = max_ngram
            self.shared_expressions = []

        else: 
            self.history = []  
            self.length = 0
            self.window = self.length

            # speakers
            self.persons = {} 
            

            # function words seem to be discarded by the tool as non-essential to tracking lexical alignment
            self.exception_tokens = []

            # definitions for n_gram lengths, needed for potential optimization of n_gram calculation
            self.min_ngram = 1
            self.max_ngram = None

            # shared expressions
            self.shared_expressions = []

            # output file
            self.output_file = "conversation_output.txt"

        self.lexicon_of_shared_expressions = {}
        self.suppress_debug = suppress_debug  # Debug suppression flag

    def parallel_score(self, utterances, speaker, scoring_condition):
        """
        parallel scoring to the external module.
        """
        previous_debug_state = self.suppress_debug
        # Suppress debug during parallel scoring
        self.suppress_debug = True
        try:
            results = score_utterances_in_parallel(self, utterances, speaker, scoring_condition)
        finally:
            # Restore previous state
            self.suppress_debug = previous_debug_state 
        return results

    def add_message(self, speaker, message):
        """
        Add a message to the conversation history and adapt the persons dictionary if there is a new inclusion

        Args:
            speaker (_type_): _description_
            message (_type_): _description_
        """
        # Convert speaker name to lowercase
        speaker = speaker.lower()

        if speaker not in self.persons:
            self.persons[speaker] = Person(speaker)

        # timestamp is generated each time a message is added:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.add_to_history(timestamp, speaker, message)
        self.save_conversation_message_to_file(timestamp, speaker, message)
    

    def score_message(self, speaker, message, scoring_condition, focus_conversation=None): 
        """
        Function for scoring a message in relation to the conversation.

        Args:
            speaker (_type_): _description_
            message (_type_): _description_
            scoring_condition (_type_): _description_
            focus_conversation (_type_, optional): _description_. Defaults to None.

        Raises:
            NameError: _description_

        Returns:
            _type_: _description_
        """
        try:
            # Normalize speaker name to lowercase
            speaker = speaker.lower()
            if self.length == 0:
                return 0, 0, 0
            
            if speaker not in self.persons:
                self.persons[speaker] = Person(speaker)

            if focus_conversation != None:
                for person in focus_conversation:
                    if person not in self.persons:
                        return 0,0,0
                der, dser, dee = self.sub_conversation(focus_conversation, speaker, message)
                if scoring_condition == 1:
                    self.add_message(speaker, message)
                return der, dser, dee
            else:
                if self.history:
                
                    timestamp, last_speaker, last_message = self.history[-1]
                    # self.analyze_message(last_speaker, last_message)
                self.analyze_conversation()
                

                established_expressions, personal_repetitions = self.analyze_message(speaker, message)
                
                dee = self.calculate_dee(established_expressions, message)

                der, dser = self.create_scores(speaker, message)

            if scoring_condition == 1:
                self.add_message(speaker, message)
            else:
                # removing shared expressions from array if the speaker and message are not to be added to conversastion history
                for n_gram in established_expressions:
                    self.shared_expressions.remove(n_gram)


                for n_gram in personal_repetitions:
                    self.persons[speaker].remove_repetition(n_gram)

            return der, dser, dee
        except Exception as e:
            print(f"Error in score_message: {e}")
        return 0, 0, 0

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
            return 0, 0
        
        
        print (f'This is the history {self.history}')
        self.analyze_conversation()

        established_expressions, personal_repetitions = self.analyze_message(speaker, message)
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
        
        sub_conversation = Conversation(sub_history, count, self.window, speakers, self.exception_tokens, self.min_ngram, self.max_ngram)
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
        n_gram_set = self.create_n_grams(message)

        if sub_window != None:
            window_set = sub_window
        else:
            window_set = self.history[-self.window:] if self.window > 0 else self.history

        additions = []
        individual_repetitions = []

        for i in self.lexicon_of_shared_expressions:
            self.lexicon_of_shared_expressions[i][2] = 0
        
        
        for timestamp, speaker, past_message in window_set:
            if speaker == current_speaker: 
                matching_n_grams = self.compare(past_message, n_gram_set)
                repetitions = set(self.persons[current_speaker].repetitions)
                for n_gram in matching_n_grams:
                    if n_gram not in repetitions:
                        individual_repetitions.append(n_gram)
                        self.persons[current_speaker].add_repetition(n_gram)
            else:
                matching_n_grams = self.compare(past_message, n_gram_set)
                # print (f'{speaker}: and {past_message}')
                # print(f' Matching N_grams at this point are: {matching_n_grams}')
                # print (f'S hared expressions at this point are: {self.shared_expressions}')
            
                for n_gram in matching_n_grams:
                    
                    if n_gram not in self.shared_expressions:
            
                        additions.append(n_gram)
                        
                        # manage the lexicon of shared expressions
                        self.lexicon_of_shared_expressions[n_gram] = [speaker, 2, 1]
                    if self.lexicon_of_shared_expressions[n_gram][2] == 0:
                        self.lexicon_of_shared_expressions[n_gram][1] += 1
                        self.lexicon_of_shared_expressions[n_gram][2] = 1


        self.shared_expressions += additions
        return additions, individual_repetitions



    def add_to_history(self, timestamp, speaker, message):
        """
        add a messsage to the conversation history

        Args:
            speaker (_type_): _description_
            message (_type_): _description_
        """
        self.history.append((timestamp, speaker, message))
        self.length += 1
    

    def create_scores(self, speaker, message):
        """
        Sets up the respective score calculations for DER and DSER

        Args:
            speaker (_type_): _description_
            message (_type_): _description_

        Returns:
            _type_: _description_
        """
        message = ''.join([char for char in message if char.isalnum() or char.isspace()])
        word_set = message.split()

        # print (f'Word set: {word_set}')

        
        if speaker in self.persons:
            person = self.persons[speaker]  
            der_score = self.calculate_der(word_set)
        else:
            print(f"No such person: {speaker}")
            return NameError

        dser_score = self.calculate_dser(word_set, person)

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
        message = ''.join([char for char in message if char.isalnum() or char.isspace()])
        word_set = message.split()
        dee = self.fraction_measurement(word_set, established_expressions)

        return dee


    def calculate_der(self, word_set):
        """
        Calculate DER measurement final step,  speaker shared established expression repetition

        Args:
            word_set (_type_): _description_

        Returns:
            _type_: _description_
        """
        der = self.fraction_measurement(word_set, self.shared_expressions)

        return der
    
    def calculate_dser(self, word_set, speaker):
        """
        Calculate DSER measurement final step, speaker personal repetition

        Args:
            word_set (_type_): _description_
            speaker (_type_): _description_

        Returns:
            _type_: _description_
        """
        used_tokens = speaker.show_repetitions()
        dser = self.fraction_measurement(word_set, used_tokens)

        return dser



    def fraction_measurement(self, word_set, used_tokens):
        """
        Measures the amount of a word_set that is comprised of a set of tokens defined by used_tokens and 
        returns the percentage composition.

        Args:
            word_set (_type_): _description_
            used_tokens (_type_): _description_

        Returns:
            _type_: _description_
        """
        tracking_arr = [0] * len(word_set)  
        
        for i in used_tokens:


            words_in_i = i.split()  
            
            if len(words_in_i) == 1:  
                for count, word in enumerate(word_set):
                    if words_in_i[0] == word: 
                        tracking_arr[count] = 1
            
            elif len(words_in_i) > 1:
                for count in range(len(word_set) - len(words_in_i) + 1):
                    match = True
                    for offset, word in enumerate(words_in_i):
                        if count + offset >= len(word_set) or word_set[count + offset] != word:
                            match = False
                            break

                    if match:
                        for offset in range(len(words_in_i)):
                            tracking_arr[count + offset] = 1

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
            matching_n_grams = [n_gram for n_gram in n_gram_set if n_gram in past_n_grams]
            return matching_n_grams
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
            message = ''.join([char for char in message if char.isalnum() or char.isspace()]) # strips punctuation
            # message = message.replace('.', ' .')
            # message = message.replace(',', ' ,')
            words = message.split()
            n_grams = set()
            
            # checking against max_ngram value to apply appropriate constraints
            if self.max_ngram == None:
                maximum = len(words)
            else:
                maximum = self.max_ngram

            # Generate n-grams of size minimum to size maximum (those being variable defined in __init__
            for i in range(len(words)):
                for n in range(self.min_ngram, maximum + 1):
                    n_gram = ' '.join(words[i:i+n])
                    n_grams.add(n_gram)
            
            n_grams = list(n_grams)
            #print (f'Length of n_grams = {len(n_grams)}')



            # for n in range(1, maximum + 1):
            #     for i in range(maximum - n + 1):
            #         n_gram = ' '.join(words[i:i+n])
            #         n_grams.append(n_gram)
            
            # remove exception tokens
            n_grams_without_exceptions = []
            for h in n_grams:
                if h not in self.exception_tokens:
                    n_grams_without_exceptions.append(h)

            return n_grams_without_exceptions
        except ValueError: 
            print ("Invalid message argument provided to n_gram factoring")


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

    def set_window(self, window):
        """
        Sets a window size of past statements. Only statements in window size are measured. 

        Args:
            window (_type_): _description_
        """
        """Return a filtered view of the conversation history based on a count or time window."""
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

    
    def show_conversation(self):
        """
        test function to see conversation history if necessary
        """
        print("\nConversation history:")
        for i in self.history:
            print (i)
        # for speaker, message in self.history:
        #     print(f"{speaker}: {message}")
    

    def analyze_conversation(self):
        window_set = self.history[-self.window:]
        self.shared_expressions = []
        count = 0
        sub_window = []
        for timestamp, speaker, message in window_set:
            if count > 0:
                self.analyze_message(speaker, message, sub_window)
            sub_window.append((timestamp, speaker, message))
            count += 1

        if not self.suppress_debug:  # Check debug suppression flag
            print(self.lexicon_of_shared_expressions)

    def conversation_information(self):
        """
        print information about a conversation such as repetion amoung individual locutors as well as general shared expressions
        """
        print("")
        print (f'Shared Expressions: {self.shared_expressions}')

        print("")
        print ("Personal Repetitions amoung speakers")
        for person in self.persons.values():
            person.print_repetitions()


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
                #print (f'Shared Expressions : {self.shared_expressions}')
                if self.length == 0:
                    return 0,0,0
                
                if focus_conversation == None:
                    der, dser, dee = self.score_message(speaker, message, scoring_condition)
                else:
                    der, dser, dee = self.score_message(speaker, message, scoring_condition, focus_conversation)
                print (f'Shared Expressions : {self.shared_expressions}')
                self.analyze_conversation()
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

        elif mode == 'p':
            results = conversation.parallel_score(utterances_to_score, "BatchSpeaker", 0)
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
            
            
if __name__ == '__main__':
    utterances_to_score = [
        "We can divide how much it cost to buy fifteen hot dog by fifteen.",
        "I see what you're saying. So, we have three over forty. Do you think multiplying is the right approach?",
        "Got it. With three over forty, do you think multiplying is the correct method?",
        "I get it now. So, with three over forty, do you think we should multiply?",
        "Okay, so we have three over forty. Do you agree that multiplying is the way to go?",
    ]
    conversation = Conversation()
    input_file = "conversation_input.txt"
    conversation.load_conversation_from_file(input_file)
    # conversation.set_n_gram_length_characteristics(3, 3)
    while True:


        mode = input("Enter option (a, s, q, w, p) ")
        if mode == 'q':
            break
        elif mode == 'p':
            speaker = "BatchSpeaker"
            conversation.request('p', speaker)
        else:
            speaker = input("Enter speaker: ").strip().lower()
            message = input("Enter message: ").strip
        
            conversation.request(mode, speaker, message, 1)
        conversation.show_conversation()
        #conversation.conversation_information()
    


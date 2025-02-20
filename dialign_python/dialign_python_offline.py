import re
from collections import Counter
import pprint
import pandas as pd
import numpy as np
import spacy
from scipy.stats import entropy
from person import Person
from conversation import Conversation

nlp = spacy.load("en_core_web_sm")

def read_transcript(input_file: str, speaker_col: str, message_col: str, sheet_name=None, valid_speakers=None, filters=None):
    """
    Function to read a conversation transcript from a file.

    Args:
        input_file (str): Path to the input file containing the conversation data.
        speaker_col (str): Name of the column containing the speaker data.
        message_col (str): Name of the column containing the message data.
        timestamp_col (str, optional): Name of the column containing the timestamp data. Defaults to None.
        valid_speakers (list, optional): List of valid speakers to include in the analysis. Defaults to None.
        sheet_name (str, optional): Name of the sheet to read from the input file. Defaults to None.
        filters (dict, optional): Dictionary of filters to apply to the conversation data. Defaults to None.

    Returns:
        df (pd.DataFrame): DataFrame containing the conversation data.
    """
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
        input_file (str): Path to the input file containing the conversation data.
        speaker_col (str): Name of the column containing the speaker data.
        message_col (str): Name of the column containing the message data.
        timestamp_col (str, optional): Name of the column containing the timestamp data. Defaults to None.
        valid_speakers (list, optional): List of valid speakers to include in the analysis. Defaults to None.
        sheet_name (str, optional): Name of the sheet to read from the input file. Defaults to None.
        filters (dict, optional): Dictionary of filters to apply to the conversation data. Defaults to None.
        window (int | timedelta, optional): Count or time window for the conversation history. Defaults to None.
        exception_tokens (list, optional): List of tokens to exclude from the analysis. Defaults to None.
        min_ngram (int, optional): Minimum n-gram length for the analysis. Defaults to 1.
        max_ngram (int, optional): Maximum n-gram length for the analysis. Defaults to None.
        suppress_debug (bool, optional): Flag to suppress debug output. Defaults to False.

    Returns:
        speaker_independent (dict): Dictionary containing the speaker-independent scores (ER, SER, EE, Total tokens, Num. shared expressions) for the conversation.
        speaker_dependent (dict): Dictionary containing the speaker-dependent scores (ER, SER, EE, Total tokens, Initiated, Established) for each `valud_speaker` for the conversation.
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
    pprint.pprint(online_metrics)
    print("Self repetitions:")
    for speaker, data in self_repetitions.items():
        print(f"{speaker}: {data}")
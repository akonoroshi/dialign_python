from collections import Counter
import pprint
import pandas as pd
import numpy as np
from scipy.stats import entropy
from dialign_python.person import Person
from dialign_python.conversation import Conversation


def read_transcript(input_file: str, speaker_col: str, message_col: str, sheet_name=None, valid_speakers=None,
                    filters=None):
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


def _get_ev(expressions: list, total_tokens: int):
    return len(expressions) / total_tokens


def _get_entr(expressions: list):
    expression_lengths = [len(expression.split()) for expression in expressions]
    counter = Counter(expression_lengths)
    _, counts = zip(*counter.items())
    probabilities = np.array(counts) / len(expression_lengths)
    return float(entropy(probabilities))


def dialign(input_file: str, speaker_col: str, message_col: str, timestamp_col=None, valid_speakers=None,
            sheet_name=None, filters=None, window=None, exception_tokens=None, min_ngram=1, max_ngram=None,
            time_format="%Y-%m-%d %H:%M:%S", tokenizer=None):
    """
    Function to run the Dialign algorithm on a conversation dataset.

    Args: input_file (str): Path to the input file containing the conversation data. speaker_col (str): Name of the
    column containing the speaker data. message_col (str): Name of the column containing the message data.
    timestamp_col (str, optional): Name of the column containing the timestamp data. Defaults to None. valid_speakers
    (list, optional): List of valid speakers to include in the analysis. Defaults to None. sheet_name (str,
    optional): Name of the sheet to read from the input file. Defaults to None. filters (dict, optional): Dictionary
    of filters to apply to the conversation data. Defaults to None. window (int | timedelta, optional): Count or time
    window for the conversation history. Defaults to None. exception_tokens (list, optional): List of tokens to
    exclude from the analysis. Defaults to None. min_ngram (int, optional): Minimum n-gram length for the analysis.
    Defaults to 1. max_ngram (int, optional): Maximum n-gram length for the analysis. Defaults to None. time_format (
    str, optional): format of the timestamp. Defaults to "%Y-%m-%d %H:%M:%S". tokenizer (function, optional):
    Tokenizer function to use for the analysis. It must take a string to tokenize as the only argument and return a
    list of tokens. Defaults to tokenize in utils.py.

    Returns: tuple: A tuple containing the following elements: - speaker_independent (dict): Dictionary containing
    the speaker-independent scores (EV, ER, ENTR, L, LMAX, SER, EE, Total tokens, Num. shared expressions) for the
    conversation. - speaker_dependent (dict): Dictionary containing the speaker-dependent scores (ER, EE,
    Total tokens, Initiated, Established) for each speaker for the conversation. - shared_expressions (dict):
    Dictionary containing the shared expressions. Keys are shared expressions, and values are dictionaries containing
    the initiator, establisher, establishment turn, and turns in which the expression appeared. - self_repetitions (
    dict): Dictionary containing the self-repetition scores (SEV, SER, SENTR, SL, SLMAX) for each speaker for the
    conversation. - online_metrics (list): List of dictionaries containing the online metrics for each message in the
    conversation.
    """

    if tokenizer is None:
        from dialign_python.utils import tokenize
        tokenizer = tokenize

    df = read_transcript(input_file, speaker_col, message_col, sheet_name, valid_speakers, filters)

    # Initialize the conversation instance
    if valid_speakers is None:
        valid_speakers = df[speaker_col].unique()
    persons = {speaker: Person(speaker) for speaker in valid_speakers}
    conversation = Conversation(persons=persons, window=window, exception_tokens=exception_tokens, min_ngram=min_ngram,
                                max_ngram=max_ngram, time_format=time_format)

    # Iterate through each row in the conversation data
    repetition_num = 0
    self_repetition_num = 0
    establishment_num = 0
    total_tokens = 0
    speaker_dependent = {speaker: {"ER": 0, "EE": 0, "Total tokens": 0, "Initiated": 0, "Established": 0} for speaker in
                         valid_speakers}
    self_repetitions = {speaker: {"SER": 0} for speaker in valid_speakers}
    online_metrics = []
    for _, row in df.iterrows():
        speaker = row[speaker_col]
        tokens = tokenizer(row[message_col])
        message = ' '.join(tokens).lower()
        if timestamp_col is not None:
            timestamp = row[timestamp_col]
            der, dser, dee, established_expression, repeated_expression, self_repetition = conversation.score_message(
                speaker, message, timestamp, add_message_to_history=True)
        else:
            der, dser, dee, established_expression, repeated_expression, self_repetition = conversation.score_message(
                speaker, message, add_message_to_history=True)
        speaker_dependent[speaker]["ER"] += round(der * len(tokens))
        self_repetitions[speaker]["SER"] += round(dser * len(tokens))
        speaker_dependent[speaker]["EE"] += round(dee * len(tokens))
        speaker_dependent[speaker]["Total tokens"] += len(tokens)
        repetition_num += round(der * len(tokens))
        self_repetition_num += round(dser * len(tokens))
        establishment_num += round(dee * len(tokens))
        total_tokens += len(tokens)
        online_metrics.append({'Speaker': speaker, 'Message': message, 'DER': der, 'DSER': dser, 'DEE': dee,
                               'Established Expression': established_expression,
                               'Repeated Expression': repeated_expression, 'Self Repetition': self_repetition})

    # Compute the final speaker-dependent scores
    for speaker in valid_speakers:
        if speaker_dependent[speaker]["Total tokens"] > 0:
            speaker_dependent[speaker]["ER"] /= speaker_dependent[speaker]["Total tokens"]
            self_repetitions[speaker]["SER"] /= speaker_dependent[speaker]["Total tokens"]
            speaker_dependent[speaker]["EE"] /= speaker_dependent[speaker]["Total tokens"]
        else:
            speaker_dependent[speaker]["ER"] = 0
            self_repetitions[speaker]["SER"] = 0
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
    speaker_independent['EV'] = _get_ev(conversation.shared_expressions.keys(), total_tokens)
    expression_lengths = [len(expression.split()) for expression in conversation.shared_expressions]
    speaker_independent['ENTR'] = _get_entr(conversation.shared_expressions.keys())
    speaker_independent['L'] = float(np.mean(expression_lengths))
    speaker_independent['LMAX'] = int(np.max(expression_lengths))

    # Compute the self-repetitions
    for speaker, person in conversation.persons.items():
        self_repetitions[speaker]["SEV"] = _get_ev(person.show_repetitions(),
                                                   speaker_dependent[speaker]["Total tokens"])
        expression_lengths = [len(expression.split()) for expression in person.show_repetitions()]
        self_repetitions[speaker]["SENTR"] = _get_entr(person.show_repetitions())
        self_repetitions[speaker]["SL"] = float(np.mean(expression_lengths))
        self_repetitions[speaker]["SLMAX"] = int(np.max(expression_lengths))

    return speaker_independent, speaker_dependent, conversation.shared_expressions, self_repetitions, online_metrics


if __name__ == "__main__":
    # Example usage of the dialign function
    input_file = "sample_offline_input.csv"
    speaker_col = "Speaker"
    message_col = "Utterance"
    timestamp_col = "Timestamp"
    valid_speakers = ["Emma", "Student A", "Student B"]
    filters = {'Receiver': valid_speakers}
    time_format = "%H:%M:%S.%f"
    speaker_independent, speaker_dependent, shared_expressions, self_repetitions, online_metrics = \
        dialign(input_file,
                speaker_col,
                message_col,
                timestamp_col,
                valid_speakers,
                filters=filters,
                time_format=time_format)
    print(f"Speaker independent: {speaker_independent}")
    print("Speaker dependent:")
    for speaker, data in speaker_dependent.items():
        print(f"{speaker}: {data}")
    pprint.pprint(f"Shared expressions: {shared_expressions}")
    pprint.pprint(online_metrics)
    print("Self repetitions:")
    for speaker, data in self_repetitions.items():
        print(f"{speaker}: {data}")

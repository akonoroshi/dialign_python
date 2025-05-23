from dialign_python.dialign_python_offline import dialign

input_file = "./dialign_python/sample_offline_input.csv"
speaker_col = "Speaker"
message_col = "Utterance"
timestamp_col = "Timestamp"
valid_speakers = ["Emma", "Student A", "Student B"]
filters = {'Receiver': valid_speakers}
time_format="%H:%M:%S.%f"

def test_dialign_offline():
    speaker_independent_expected = {
        'ER': 0.21140939597315436,
        'SER': 0.2214765100671141,
        'EE': 0.0738255033557047,
        'Total tokens': 298,
        'Num. shared expressions': 19,
        'EV': 0.06375838926174497,
        'ENTR': 0.40945861869508926,
        'L': 1.1578947368421053,
        'LMAX': 3
    }
    speaker_dependent_expected = {
        'Emma': {'ER': 0.22807017543859648, 'EE': 0.03508771929824561, 'Total tokens': 114, 'Initiated': 0.5789473684210527, 'Established': 0.21052631578947367},
        'Student A': {'ER': 0.1388888888888889, 'EE': 0.09722222222222222, 'Total tokens': 72, 'Initiated': 0.2631578947368421, 'Established': 0.3684210526315789},
        'Student B': {'ER': 0.24107142857142858, 'EE': 0.09821428571428571, 'Total tokens': 112, 'Initiated': 0.15789473684210525, 'Established': 0.42105263157894735}
    }
    speaker_independent, speaker_dependent, shared_expressions, self_repetitions, online_metrics = dialign(input_file, speaker_col, message_col, timestamp_col, valid_speakers, filters=filters, time_format=time_format)

    assert speaker_independent == speaker_independent_expected
    assert speaker_dependent == speaker_dependent_expected

# dialign_python

This repository has the multi-party version of [dialign](https://github.com/GuillaumeDD/dialign) (Dubuisson Duplessis et al., 2021) implemented in Python. The extension to multi-party dialogues is under review at AIED 2025 (Anonymous, 2025).

## Framework
![image](https://github.com/user-attachments/assets/54e9cf16-b8ec-4b7a-92d0-e22407e1a19d)

Our proposed measure extends the notion of shared expressions (Dubuisson Duplessis et al., 2017,2021) to multi-party dialogues. We re-define *shared expressions* as "a surface text pattern inside an utterance that has been produced by **all** speakers, **regardless of to whom they spoke**. An expression can either be
free or constrained, the same as Duplessis et al. (2017); an expression is *free* when it appears in an utterance without being a subexpression of a larger expression, whereas an expression is *constrained* if it appears in a turn as a subexpression of a larger expression (e.g., "two" in "two over three" in the table above). In our definition, a shared expression is *established* when it has been produced by all speakers and at least once in a free form.

Duplessis et al. (2017) define the *initiator* of an expression as, "the interlocutor that first produced an instance of the expression." Similarly, we define the *establisher* as the last interlocutor that produced an instance of the expression, i.e., the interlocutor that established the shared expression in their turn. Note that the acts of initiation and establishment do not have any constraints on the number of turns.

`dialign_python` offers self-repetitions, too (Dubuisson Duplessis et al., 2021). "Self-repetitions are lexical patterns appearing at least twice in the dialogue utterances of a given \[speaker\], independently of the other \[speakers'\] utterances."

### Metrics provided by `dialign_python`
The following explanations are taken from [dialign](https://github.com/GuillaumeDD/dialign) (Dubuisson Duplessis et al., 2021), Asano et al. (2022) Anonymous (2025).
`dialign_python` provides a set of measures to characterise both:
1. the interactive verbal alignment process between dialogue participants, and
2. the self-repetition behaviour of each participant.

These measures allow the characterisation of the nature of these processes by addressing 
various informative aspects such as their variety, strength, complexity, stability, and 
orientation. In a nutshell:
- **variety**: the variety of shared expressions or self-repetitions emerging during a dialogue 
               relative to its length. It is directly related to the number of unique 
               expressions in a lexicon. 
- **strength**: the strength of repetition of the (shared) lexical patterns, i.e., how much the
                patterns are reused.
- **complexity**: the complexity indicates the variety of the types of lexical patterns. It is here 
                  featured by Shannon entropy measures. High entropy indicates the presence of
                  a wide range of lexical patterns relative to their lengths in number of tokens (e.g., ranging 
                  from a single word to a full sentence). On the contrary, low entropy indicates the predominance 
                  of one type of lexical pattern.
- **extension** and **stability**: the extension and stability of the (shared) lexical patterns are related 
                                   to the size of the lexical patterns. The extension indicates the size of the 
                                   lexical patterns. The longer it is, the more extended the lexical pattern is. 
                                   Extension is directly linked to the stability of the processes since the 
                                   more extended the patterns are, the more stable the processes are.
- **orientation**: the orientation of the interactive alignment process, i.e., it indicates either a symmetry 
                   (both dialogue participants initiate and reuse the same number of shared lexical patterns),
                   or an asymmetry (a dialogue participant initiates and/or reuses more shared lexical patterns).
- **activeness**: the activeness of speakers in the establishment of shared lexical patterns.

#### Speaker-independent
| Measure | Description |  Aspects |
| :---:   | :---       |  :---:   |
|  EV     |  Expression Variety (EV). The shared expression lexicon size normalized by the length of the dialogue (which is its total number of tokens in the dialogue).  | Variety | 
|  ER     |  Expression Repetition (ER). The proportion of tokens which speakers dedicate to the repetition of a shared expression.  | Strength |
| ENTR    | Shannon entropy of the lengths in token of the shared expression instances. | Complexity |
| L       | Average length in token of the shared expression instances. | Stability |
| LMAX    | Maximum length in token of the shared expression instances. | Stability |
| EE      | Expression Establishment (EE). The proportion of tokens which speakers dedicate to the establishment of a shared expression. | Activeness |

#### Speaker-dependent

| Measure | Description |  Aspects |
| :---:   | :---       |  :---:   |
|  IE_S     |  Initiated Expression (IE) for locutor S. Ratio of shared expressions initiated by locutor S.   | Orientation | 
|  ER_S     |  Expression Repetition (ER) for locutor S. Ratio of tokens produced by S belonging to an instance of a shared expression.  | Strength |
|  EE_S     |  Expression Establishment (EE) for locutor S. Ratio of tokens produced by S used to establish a new shared expression.  | Activeness |
|  EsE_S    |  Established Expression (EsE) for locutor S. Ratio of shared expressions established by locutor S.   | Orientation |

### Measures Characterising Self-Repetition Behaviour of each Dialogue Participant
| Measure | Description |  Aspects |
| :---:   | :---       |  :---:   |
|  SEV_S  |  Self-Expression Variety (SEV) for locutor S. For locutor S, the self-repetition lexicon size normalized by the total number of tokens produced by S in the dialogue.  | Variety | 
|  SER_S     |  Self-Expression Repetition (SER) for locutor S. The proportion of tokens which locutor S dedicates to self-repetition.| Strength |
| SENTR_S    |  Shannon entropy of the length in token of the self-repetitions from S. | Complexity |
| SL_S       |  Average length in tokens of the self-repetitions from S. | Stability |
| SLMAX_S    |  Maximum length in token of the self-repetitions from S. | Stability |

### Synthetic Presentation of the Provided Measures
| Aspect      | Speaker-independent Measures (*) | Speaker-dependent Measures (**) |
| :---:       | :---:                            | :---:                           |
| Variety     | EV                               |  SEV_S                          | 
| Strength    | ER                               |  ER_S, SER_S                    |
| Complexity  | ENTR                             |  SENTR_S                        |
| Stability   | L, LMAX                          |  SL_S, SLMAX_S                  |
| Orientation |  --                              |  IE_S, EsE_S                    |
| Activeness  | EE                               |  EE_S                           |

(*) All these measures are related to the interactive verbal alignment process

(**) Measures starting with 'S' are related to the self-repetition behaviour, the others
     are related to the interactivate verbal alignment process


## Installation
After cloning this repo, go to the top directory of the repo and run the following:
```
python -m pip install .
```

## Usage
There are two modes: offline and online. The offline mode is designed for the analysis of completed dialogues (in other words, you should have transcripts of finished dialogues). The online mode is designed for ongoing dialogues. The online mode can score new utterances using the dialogue history and update the history in real-time.

### Offline mode


### Online mode


## References
- Anonymous, Multi-party Lexical Alignment in Collaborative Learning with a Teachable Robot, under review at 26th International Conference on Artificial Intelligence in Education, 2025.
- Asano, Y.; Litman, D.; Yu, M.; Lobczowski, N.; Nokes-Malach, T.; Kovashka, A.; & Walker, E., Comparison of Lexical Alignment with a Teachable Robot in Human-Robot and Human-Human-Robot Interactions. In Proceedings of the 23rd Annual Meeting of the Special Interest Group on Discourse and Dialogue, 2022 pp. 615-622. https://aclanthology.org/2022.sigdial-1.57/
- Dubuisson Duplessis, G.; Langlet, C.; Clavel, C.; Landragin, F., Towards alignment strategies in human-agent interactions based on measures of lexical repetitions, Lang Resources & Evaluation, 2021, 36p. https://dx.doi.org/10.1007/s10579-021-09532-w
- Dubuisson Duplessis, G.; Clavel, C.; Landragin, F., Automatic Measures to Characterise Verbal Alignment in Human-Agent Interaction, 18th Annual Meeting of the Special Interest Group on Discourse and Dialogue (SIGDIAL), 2017, pp. 71--81. https://aclanthology.org/W17-5510/

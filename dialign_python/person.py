class Person:
    def __init__(self, name):
        """
        Initializes a person in the conversation

        Args:
            name (_type_): _description_
        """
        self.name = name
        self.repetitions = []  # Store personal repetitions

    def add_repetition(self, n_gram):
        """
        Add a n_gram that is repeated within Person's conversation history (contributing to DSER score)

        Args:
            n_gram (_type_): _description_
        """
        self.repetitions.append(n_gram)

    def remove_repetition(self, n_gram):
        """
        removes an n_gram from the Person's expression library

        Args:
            n_gram (_type_): _description_
        """
        self.repetitions.remove(n_gram)

    def show_repetitions(self):
        """
        Show all repetitions of Person

        Returns:
            _type_: _description_
        """
        return self.repetitions

    def print_repetitions(self):
        print(f'{self.name}: {self.repetitions}')

    def get_name(self):
        """
        Get the name of the person

        Returns:
            _type_: _description_
        """
        return self.name

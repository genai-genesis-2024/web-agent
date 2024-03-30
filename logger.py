import json
import random
import os
from prettytable import PrettyTable

class Experiment:
    def __init__(self, prompt, data=None):
        if data is None:
            data = {}
        self.id = str(random.randint(10000, 99999)) 
        self.prompt = prompt
        self.data = data

class LlmLogger:
    def __init__(self, file_path):
        self.experiments = []
        self.file_path = file_path

    def load_experiments(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                self.experiments = json.load(file, object_hook=lambda d: Experiment(**d))
        else:
            with open(self.file_path, 'w') as file:
                json.dump(self.experiments, file)

    def save_experiments(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.experiments, file, default=lambda o: o.__dict__)

    def log_experiment(self, prompt):
        experiment = Experiment(prompt)
        self.experiments.append(experiment)
        self.save_experiments()
        return experiment.id

    def log_data(self, id, column, value):
        for experiment in self.experiments:
            if experiment.id == id:
                experiment.data[column] = value
                self.save_experiments()
                break
        else:
            print("Experiment ID not found")

    def display_experiments_table(self):
        table = PrettyTable()
        keys = set(key for exp in self.experiments for key in exp.data.keys())
        keys = sorted(keys)

        columns = ['ID', 'Prompt'] + list(keys)
        table.field_names = columns

        for exp in self.experiments:
            row = [exp.id, exp.prompt] + [exp.data.get(key, '') for key in keys]
            table.add_row(row)

        print(table)

# Usage Example
logger = LlmLogger('experiments.json')
logger.load_experiments()
experiment_id = logger.log_experiment('Test prompt')
logger.log_data(experiment_id, 'Result', 'Success')
logger.display_experiments_table()

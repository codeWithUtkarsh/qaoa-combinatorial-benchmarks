import csv
import numpy as np


def get_average(lst: list[int]):
    return sum(lst) / len(lst)


def load_data(dir_name: str, file_name: str):
    file_path = dir_name + "/" + file_name
    data = []

    with open(file_path, "r", newline="") as csvfile:
        file_reader = csv.reader(
            csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

        # skip header
        next(file_reader)

        for lines in file_reader:
            data.append(int(lines[1]))

    return data


def rm_outliers(data: list[int]) -> list[int]:
    """
    removes outliers from the list
    """

    k = 1.5

    q1 = np.percentile(data, 25)  # Q1
    q3 = np.percentile(data, 75)  # Q3
    iner_quartile = q3 - q1
    lower_bound = q1 - k * iner_quartile
    upper_bound = q3 + k * iner_quartile

    data_rm = filter(lambda x: x > lower_bound and x < upper_bound, data)
    return list(data_rm)


def save_results(results, dir_name, file_name):
    file_path = dir_name + "/" + file_name

    with open(file_path, "w", newline="") as csvfile:
        file_writer = csv.writer(
            csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

        file_writer.writerows(results)


def main():
    dir_name = "./results/results-for-report"

    result_files = [
        "m6_atsp.csv",
        "m9_atsp.csv",
        "m12_atsp.csv",
        "burma14_tsp.csv",
        "br17_atsp.csv",
        "gr21_tsp.csv",
        "gr24_tsp.csv",
    ]

    file_name = "gr24_tsp.csv"

    results = []
    for file_name in result_files:
        data = load_data(dir_name, file_name)
        data_rm = rm_outliers(data)
        average = get_average(data_rm)
        average = round(average, 2)
        results.append([file_name, average])

    print(results)

    save_results(results, "./", "results_average.csv")


if __name__ == "__main__":
    main()

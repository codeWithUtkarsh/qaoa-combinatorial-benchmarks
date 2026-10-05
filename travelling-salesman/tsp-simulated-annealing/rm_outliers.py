import csv

import numpy as np


def get_average(lst: list[int]):
    print(lst)
    return sum(lst) / len(lst)


def load_data(dir_name: str, file_name: str):
    file_path = dir_name + "/" + file_name
    time_list = []
    prd_list = []

    vertexCount: int = -1

    with open(file_path, "r", newline="") as csvfile:
        file_reader = csv.reader(
            csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

        # skip header
        next(file_reader)

        for lines in file_reader:
            vertexCount = int(lines[1])
            time_list.append(int(lines[2]))
            prd_list.append(float(lines[5]))

    print(prd_list)

    return time_list, prd_list, vertexCount


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
        file_writer.writerow(
            ["instance name", "vertex count", "average time [ns]", "average prd [%]"]
        )
        file_writer.writerows(results)


def main():
    dir_name = "./results"

    instance_names = [
        "m6.atsp",
        "m10.atsp",
        "burma14.tsp",
        "gr24.tsp",
        "bays29.tsp",
        "ftv33.atsp",
        "ftv44.atsp",
        "att48.tsp",
        "berlin52.tsp",
        "ftv70.atsp",
        "gr96.tsp",
        "kroA100.tsp",
        "gr120.tsp",
        "pr124.tsp",
        "kroB150.tsp",
        "pr152.tsp",
        "ftv170.atsp",
        "kroB200.tsp",
        "rbg323.atsp",
    ]

    results = []
    for instance_name in instance_names:

        file_name = f"{instance_name}.csv"
        time_list, prd_list, vertexCount = load_data(dir_name, file_name)
        time_list = rm_outliers(time_list)

        average_time = get_average(time_list)
        # average_prd = get_average(prd_list)
        average_prd = min(prd_list)

        average_time = round(average_time, 2)
        average_prd = round(average_prd, 2)

        results.append([instance_name, vertexCount, average_time, average_prd])

    save_results(results, "./", "results_average.csv")


if __name__ == "__main__":
    main()

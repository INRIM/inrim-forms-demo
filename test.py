data = {
    "textArea": 'test a',
    "number": '1',
    "x": 'X',
    "y": 'y',
    'dataGrid_dataGridRow_0-textField': 'a1',
    'dataGrid_dataGridRow_0-2': 'b1',
    'dataGrid_dataGridRow_0-3': 'c1',
    'dataGrid_dataGridRow_0-select1': 'x',
    'dataGrid_dataGridRow_0-dateTime': '04/03/2021',
    'dataGrid_dataGridRow_1-textField': 'b1',
    'dataGrid_dataGridRow_1-2': 'b2',
    'dataGrid_dataGridRow_1-3': 'b3',
    'dataGrid_dataGridRow_1-select1': 'y',
    'dataGrid_dataGridRow_1-dateTime': '05/03/2021',
    'dataGrid_dataGridRow_2-textField': 'c1',
    'dataGrid_dataGridRow_2-2': 'c2',
    'dataGrid_dataGridRow_2-3': 'c3',
    'dataGrid_dataGridRow_2-select1': 'z',
    'dataGrid_dataGridRow_2-dateTime': '06/03/2021'
}
key = "dataGrid"
c_key = "dataGridRow"
c_keys = ["textField", "2", "3", "select1", "dateTime"]
list_to_pop = []
new_dict = {
    key: []
}
last_group = False
data_row = {}
for k, v in data.items():
    if f"{key}_" in k:
        list_to_pop.append(k)
        list_keys = k.split("-")
        if list_keys:
            groups = list_keys[0].split("_")
            if groups[2] != last_group:
                if last_group:
                    new_dict[key].append(data_row.copy())
                    data_row = {}
                last_group = groups[2]
            if list_keys[1] in c_keys:
                data_row[k] = data[k]
new_dict[key].append(data_row.copy())
for i in list_to_pop:
    data.pop(i)
data = {**data, **new_dict}

print(data)

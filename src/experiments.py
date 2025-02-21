from flet.security import encrypt, decrypt

secret_key = "BABABABA"

tasks = [
            {"task_name": "taskk", "completed": False},
            {"task_name": "taskk2", "completed": False},
            {"task_name": "taskk3", "completed": False}
        ]

for task in tasks:
    task["task_name"] = encrypt(task["task_name"], secret_key)

print("TASKS encrypted:", tasks, "\n")

for task in tasks:
    task["task_name"] = decrypt(task["task_name"], secret_key)

print("TASKS DECRYPTED:", tasks, "\n")

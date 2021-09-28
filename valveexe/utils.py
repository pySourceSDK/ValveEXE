import psutil

def find_process(exeName):
    return next((p for p in psutil.process_iter() if
                p.name() == exeName), None)

def terminate_process(exeName):
    process = find_process(exeName)
    process and process.terminate()
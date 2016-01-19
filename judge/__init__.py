import os
import subprocess
import glob
import math

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import DATABASE_URI

from judge.config import COMPILER_LIST
from judge.config import COMPILER_OPTION_LIST
from judge.config import COMPILER_FILEEXT_LIST
from judge.config import COMPILE_TIME_LIMIT
from judge.config import JUDGE_BIN_PATH

engine = create_engine(DATABASE_URI, echo=True)
DB_Session = sessionmaker(bind=engine)
session = DB_Session()
BaseModel = declarative_base()

def compile(source_path, compiler_id, exec_path): #print("[log] compile:")
    #print(COMPILER_LIST[compiler_id])
    #print(source_path)
    #print(COMPILER_OPTION_LIST[compiler_id])
    proc = subprocess.Popen([COMPILER_LIST[compiler_id],
        source_path,
        *COMPILER_OPTION_LIST[compiler_id]],
        cwd = exec_path,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE)
    try:
        outs, err = proc.communicate(timeout = COMPILE_TIME_LIMIT)
        returncode = proc.returncode
    except:
        proc.kill()
        out, err = proc.communicate()
        returncode = proc.returncode
    return (returncode, exec_path + "/a.out", err.decode('utf-8'))

def execute(program, input_file, output_file, time_limit, memory_limit, exec_path):
    #print("execute:")
    #print(["judge/run", "-c", program, "-i", input_file, "-o", output_file, "-t", str(time_limit), "-m", str(memory_limit), "-d", exec_path])
    proc = subprocess.Popen(
        [JUDGE_BIN_PATH, "-c", program, "-i", input_file, "-o", output_file, "-t", str(math.ceil(time_limit/1000)), "-m", str(memory_limit), "-d", exec_path],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE)
    (out, err) = proc.communicate()
    returncode = proc.returncode

    out = out.decode('utf-8').rstrip().split(',')

    return (returncode, out, err)

def check(file_out, std_out):
    proc = subprocess.Popen(["diff", file_out, std_out],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = proc.communicate()
    returncode = proc.returncode
    if returncode == 0:
        return (True, "")
    return (False, out.decode('utf-8'))

def judge_program(source_path, testcase_folder, compiler_id, time_limit, memory_limit):
    from tempfile import TemporaryDirectory
    tmp_folder = TemporaryDirectory()
    import shutil
    ori_source_path = source_path
    source_path = os.path.join(tmp_folder.name,
            'a' + COMPILER_FILEEXT_LIST[compiler_id])
    shutil.copyfile(ori_source_path, source_path)
    (returncode, prog, err) = compile(source_path, compiler_id, tmp_folder.name)
    print(returncode, prog, err)
    if returncode != 0:
        return {"verdict":"Compile Error", "time_usage": 0,
                "memory_usage": 0, "log": err[:1020], score:0}
    max_time = 0
    max_mem = 0
    def case_judge(filename):
        case_count += 1
        file_in = filename
        file_out = os.path.join(tmp_folder.name, "output.txt")
        std_out = filename[:-2] + "out"
        (returncode, out, err) = execute(prog, file_in, file_out,
                                         time_limit, memory_limit,
                                         tmp_folder.name)
        print(returncode, out, err)
        if out[0] != "OK":
            print(out)
            return {"verdict": out[0], "time_usage": out[1],
                    "memory_usage": out[2], "log": None}
        print(out[1])
        print(time_limit)
        if int(out[1]) > time_limit:
            return {"verdict": "Time Limit Exceeded", "time_usage": out[1],
                    "memory_usage": out[2], "log": None}
        (verdict, err) = check(file_out, std_out)
        if verdict == False:
            return {"verdict": "Wrong Answer", "time_usage": max_time,
                    "memory_usage": max_mem, "log": None}
        if(int(out[1]) > max_time): max_time = int(out[1])
        max_mem = max(max_mem, int(out[2]))
        return {"verdict": "Accepted", "time_usage": max_time,
                "memory_usage": max_mem, "log": None}

    ac_count = 0
    case_count = 0
    verdict = "Accepted"
    for filename in glob.glob(os.path.join(testcase_folder, "*.in")):
        verd = case_judge(filename)
        case_count += 1
        if verd["verdict"] == "Accepted":
            ac_count += 1
        if verd["verdict"] != "Accepted":
            verdict = verd["verdict"]
    if case_count == 0: case_count = 1
    score = ac_count * 100 / case_count
    return {"verdict": verdict, "time_usage": max_time,
            "memory_usage": max_mem, "log": None, "score": score}

def judge(sid, *args):
    verdict = judge_program(*args)
    return (sid,verdict)


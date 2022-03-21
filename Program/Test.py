import subprocess
import sys

output = subprocess.check_output([sys.executable, '/Users/theresawettig/PycharmProjects/2022_aCar_VRPs/Program/Execution.py'])
with open('03-21-large.txt', 'wb') as outfile:
    outfile.write(output)
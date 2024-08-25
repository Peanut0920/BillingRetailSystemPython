from cx_Freeze import setup, Executable 
 
base = None     
 
executables = [Executable("System.py", base=base)] 
 
packages = ["idna"] 
options = { 
    'build_exe': {     
        'packages':packages, 
    },     
} 
 
setup( 
    name = "POS", 
    options = options, 
    version = "31333233", 
    description = 'A POS system for ordering', 
    executables = executables 
) 
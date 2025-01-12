import datetime
from colorama import Fore, Back, Style, init
init(autoreset=True)

f = None


def open_file():
    global f
    output_path = "example/" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt")
    f = open(output_path, "w")  
    print(f"File {output_path} opened for writing.")


def write(type, txt):
    if f:

        if type == "recommendation":
            print(Back.LIGHTBLACK_EX +"[INFO] Item retrieved: " + txt + Style.RESET_ALL + "\n")
            f.write("[INFO] Item retrieved: " + txt + "\n\n")

        if type == "usr":
            print(Fore.MAGENTA + "Seeker:" + Style.RESET_ALL + " " + txt + "\n")
            f.write("Seeker: " + txt + "\n\n")

        if type=="sys":
            sys_da, sys_utt = txt
            print(Fore.YELLOW + "Recommender:" + Style.RESET_ALL + " " + Fore.GREEN + "[" + sys_da + "]" + Style.RESET_ALL + " " + sys_utt)
            f.write("Recommender: [" + sys_da + "] " + sys_utt + "\n")

        if type=="info":
            print(Fore.CYAN + txt + Style.RESET_ALL)
            f.write(txt + "\n")

        if type=="react":
            react, txt = txt
            print(Fore.LIGHTRED_EX + "[" + react + "]" + Style.RESET_ALL + " " + txt + "\n")
            f.write("[" + react + "] " + txt + "\n\n")

        if type=="query":
            print(Fore.LIGHTBLUE_EX + "Search Query:" + Style.RESET_ALL + " " + txt + "\n")
            f.write("Search Query: " + txt + "\n\n")
            
        if type=="reward":
            print(Fore.LIGHTGREEN_EX + "Reward: " + Style.RESET_ALL + txt + "\n")
            f.write("Reward: " + txt + "\n\n")

    else:
        print("File not open. Call open_file() first.")


def close_file():
    global f
    if f:
        f.close() 
        print("File closed.")
        f = None
    else:
        print("File is not open.")


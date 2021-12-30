from optparse import OptionParser

def main():
    # run for main
    parser=OptionParser()

    parser.add_option("-fr","--from",dest="from",help="initial frame")
    parser.add_option("-to","--to",dest="to",help="last frame")
    parser.add_option("-f","--file",dest="filename",help="houdini script to use",metavar="FILE")

    (options, args) = parser.parse_args()

    print(options)
    print(args)

if __name__ == "__main__":
    # begin run script
    main()

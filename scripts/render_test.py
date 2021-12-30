from optparse import OptionParser
import sys

def do_render(frm,to,inputscript,out):
    '''
        do a render
    '''
    hou.hipFile.load(inputscript)
    rnode = hou.node(out)
    rnode.render(frame_range=(frm,to))

def main():
    # run for main
    parser=OptionParser()
    debug=True

    parser.add_option("-f","--from",dest="from",help="initial frame")
    parser.add_option("-t","--to",dest="to",help="last frame")
    parser.add_option("-i","--input",dest="inputscript",help="houdini script to use",metavar="FILE")
    parser.add_option("-o","--output",dest="output",help="render engine to use")

    (options, args) = parser.parse_args()

    debug and print(options)

    do_render(options.from,options.to,options.input,options.output)

    sys.exit(0)

if __name__ == "__main__":
    # begin run script
    main()

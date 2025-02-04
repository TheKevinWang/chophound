import os
import re
import argparse
import json
import gc
try:
    import ijson.backends.python as ijson
except (ImportError, ModuleNotFoundError):
    print('Error: install the Python ijson module first')

VERSION = 1.0

def main(args):
    # Collect args
    file = args.file
    chunksize = args.chunksize
    outdir = args.output if args.output[-1] == '/' else args.output + '/'
    # Fixed variables
    basename = os.path.splitext(os.path.basename(file))[0]
    jsonformat = '{"data":[%s],"meta":%s}'

    # Open in binary mode to seek
    print('[+] Opening file %s' % file)
    with open(file, 'rb') as js:
        # Obtain meta tag
        js.seek(-0x100, os.SEEK_END)
        #this is the bug. only works in python2
        lastbytes = js.read(0x100).decode("utf-8")
        metatagstr = re.search('("meta":(\s+)?{.*})', lastbytes, re.MULTILINE | re.IGNORECASE).group(1)
        metatag = json.loads('{' + metatagstr + '}')

    # Open in text mode to parse
    with open(file, 'r', encoding='utf-8-sig', errors='replace') as js:
        items = ijson.items(js, 'data.item')

        endoflist = False
        i = 0
        while True:
            outfile = outdir + '%s_%.4d.json' % (basename, i)
            # Get chunk
            chunks = []
            count = 0
            gc.collect()
            try:
                while True:
                    item = next(items)
                    chunks.append(json.dumps(item))

                    count += 1
                    if count == chunksize:
                        break
            except StopIteration:
                endoflist = True

            # Update meta tag
            metatag['meta']['count'] = count

            # Format and store
            print('[+] Writing %s' % outfile)
            with open(outfile, 'w', encoding='utf-8-sig', errors='replace') as jsout:
                jsout.write(jsonformat % (','.join(chunks), json.dumps(metatag['meta'])))

            i += 1

            if endoflist:
                break

def getargs():
    parser = argparse.ArgumentParser(
        description='Convert large BloodHound json to smaller chunks'
    )
    parser.add_argument('file', help='JSON file to split')
    parser.add_argument('-c', '--chunksize', default=500, type=int, dest='chunksize', help='Number of items per outputted chunk')
    parser.add_argument('-o', '--output', default='./', type=str, dest='output', help='Output directory. Defaults to current directory.')

    return parser.parse_args()

if __name__ == '__main__':
    print('ChopHound v%.2f ( https://github.com/bitsadmin/chophound/ )' % VERSION)
    main(getargs())

import sys

import itk

#################################
#################################
#################################
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python ConvertImage.py <fromImage> <toImage>")
        exit()
    img = itk.imread(str(sys.argv[1]))
    itk.imwrite(img, str(sys.argv[2]),compression=True)

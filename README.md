# EXIF Parser
Parses and outputs contents of JPEG headers

# Usage

jpeg_exif.py |filename|

note: filename must be a .jpg file

# Example

jpeg_exif.py post-5k.jpg

{'ImageDescription': \['April, 6, 2019, Amherst, Massachusetts, United States:  during the Amherst Spring Fling meet. Photo by Â© Brian Foley for ClarusStudios.com.'], 'Make': \['Canon'], 'Model': \['Canon EOS-1D X'], 'XResolution': \['300/1', '72/1'], 'YResolution': \['300/1', '72/1'], 'ResolutionUnit': \[2, 2], 'Software': \['Adobe Photoshop Lightroom Classic 8.2 (Macintosh)'], 'DateTime': \['2019:04:11 12:03:24'], 'Artist': \['Geoffrey Bolte / Clarus Studios Inc.'], 'YCbCrSubSampling': \[1, 1], 'Copyright': \['(c) 2018 Clarus Studios Inc'], 'ExifIFDPointer': \[472], 'Compression': \[6], 'JPEGInterchangeFormat': \[1198], 'JPEGInterchangeFormatLength': \[5447]}

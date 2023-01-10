
# PageStream

Some scanners and PDF merge software results in a single merged PDF that has the
original document title in the outline. The dutch government uses software like
this to respond to FOIA requests.

This module was created to split these FOIA requests by outline. As an
investigative journalism platform, we encounter different kinds of pagestreams
in the wild. The intent for this module is to be a place where we collect
different functionality regarding these streams.

Example usage:
```
stream = PDFPageStream("/path/to.pdf")

if stream.can_extract_by_outline():
    stream.extract_to("/output/path")
```



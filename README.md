ITKTubeTK-CTLungs: Tubular Object Modeling for the Lungs
========================================================

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/KitwareMedical/ITKTubeTK-CTLungs/blob/master/LICENSE)

Available in Python for Linux, Windows, and MacOS.

Overview
--------

[TubeTK](https://github.com/InsightSoftwareConsortium/ITKTubeTK is an open-source toolkit for the segmentation, registration, and analysis of tubes and surfaces in images, developed by [Kitware, Inc.](http://www.kitware.com)

* [ITKTubeTK-CTLungs/src](src): This is the main application that provides
a GUI for running the algorithms.

* [ITKTubeTK-CTLungs/lib](lib): This folder contains the algorithms used for
lung segmentation and lung airway and vessel segmentation.

* [ITKTubeTK-CTLungs/experiments](experiments): This folder contains the
python notebooks that led to the development of this application.  These
are also useful for follow-on exploration for sub-tasks such as lung
segmentation.

* [ITKTubeTK-CTLungs/installer](installer): We use pyinstaller to create a
stand-alone executable for our python application, that can be run on any
machine without Python installed.  Pyinstaller support Windows, Linux, and
macOS.    Additionally, for Windows, we support Innosetup to create a
self-installable package for the executable.

Installing 
==========

We recommend using TubeTK via Python.  To do so, the installation command is

    > pip install itk-tubetk

That should bring in all of the requirements for running this application
and algorithms.

Then you can test your configuration:

    $ python -c "import itk"

and

    $ python -c "from itk import TubeTK"

Both of the above commands should execute and return without errors.   Otherwise, please post a detailed description (of what you've done and what error you received) on the TubeTK issue tracker: https://github.com/KitwareMedical/ITKTubeTK-CTLungs/issues

Acknowledgements
----------------

If you find TubeTK and this application to be useful for your work, please cite the following publication when publishing your work:
* S. R. Aylward and E. Bullitt, "Initialization, noise, singularities, and scale in height ridge traversal for tubular object centerline extraction," Medical Imaging, IEEE Transactions on, vol. 21, no. 2, pp. 61-75, 2002.

The development of TubeTK has been supported, in part, by the following grants:

* [NCI](http://www.cancer.gov/) under award numbers R01CA138419, R01CA170665, R43CA165621, and R44CA143234;
* [NIBIB](http://www.nibib.nih.gov) (NBIB) of the National Institutes of Health (NIH) under award numbers R01EB014955, R41EB015775, R43EB016621, and U54EB005149;
* [NIBIB](http://www.nibib.nih.gov) and [NIGMS](http://www.nigms.nih.gov) R01EB021396;
* [NINDS](http://www.ninds.nih.gov) R42NS086295 and R41NS081792;
* [Defense Advanced Research Projects Agency](http://www.darpa.mil) (DARPA) under the TRUST program.

License
-------

This software is distributed under the Apache 2.0 license. Please see
the *LICENSE* file for details.

References
----------

( See also [Stephen R. Aylward @ Google Scholar](https://scholar.google.com/citations?user=jHEgTSwAAAAJ&hl=en) )

* D.F. Pace, S.R. Aylward, M. Niethammer, "A Locally Adaptive Regularization Based on Anisotropic Diffusion for Deformable Image Registration of Sliding Organs," Medical Imaging, IEEE Transactions on , vol.32, no.11, pp.2114,2126, Nov. 2013 doi: 10.1109/TMI.2013.2274777
* E. Bullitt, D. Zeng, B. Mortamet, A. Ghosh, S. R. Aylward, W. Lin, B. L. Marks, and K. Smith, "The effects of healthy aging on intracerebral blood vessels visualized by magnetic resonance angiography," NEUROBIOLOGY OF AGING, vol. 31, no. 2, pp. 290-300, Feb. 2010.
* E. Bullitt, M. Ewend, J. Vredenburgh, A. Friedman, W. Lin, K. Wilber, D. Zeng, S. R. Aylward, and D. Reardon, "Computerized assessment of vessel morphological changes during treatment of glioblastoma multiforme: Report of a case imaged serially by MRA over four years," NEUROIMAGE, vol. 47, pp. T143-T151, Aug. 2009.
* E. Bullitt, K. Muller, I. Jung, W. Lin, and S. Aylward, "Analyzing attributes of vessel populations," MEDICAL IMAGE ANALYSIS, vol. 9, no. 1, pp. 39-49, Feb. 2005.
* S. Aylward, J. Jomier, S. Weeks, and E. Bullitt, "Registration and analysis of vascular images," INTERNATIONAL JOURNAL OF COMPUTER VISION, vol. 55, no. 2-3, pp. 123-138, Dec. 2003.
* E. Bullitt, G. Gerig, S. Pizer, W. Lin, and S. Aylward, "Measuring tortuosity of the intracerebral vasculature from MRA images," IEEE TRANSACTIONS ON MEDICAL IMAGING, vol. 22, no. 9, pp. 1163-1171, Sep. 2003.
* S. R. Aylward and E. Bullitt, "Initialization, noise, singularities, and scale in height ridge traversal for tubular object centerline extraction," Medical Imaging, IEEE Transactions on, vol. 21, no. 2, pp. 61-75, 2002.
* S. Aylward, S. Pizer, D. Eberly, and E. Bullitt, "Intensity Ridge and Widths for Tubular Object Segmentation and Description," in MMBIA '96: Proceedings of the 1996 Workshop on Mathematical Methods in Biomedical Image Analysis (MMBIA '96), Washington, DC, USA, 1996, p. 131.

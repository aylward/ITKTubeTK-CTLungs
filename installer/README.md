## Installation

Install the following pip packages:
```
pip install pyinstaller==4.7
```

Additionally, install ITK and TubeTK python wheels from your desired source.

You will also need to download and install Inno Setup.

## build

1. `cd Deployment; pyinstaller ITKTubeTK-CTLungs.spec` will build the app. The executable will be generated at `dist/ITKTubeTK_CTLungs_App/ITKTubeTK_CTLungs_App.exe`.
2. Run `ITKTubeTK_CTLungs_App.exe` to validate the build.
3. Open Inno Setup, open the `installer.iss` file, and run "Compile". This will generate an installer in the `Output/` folder.

## install

1. Run the installer in `Output/`. This will install a startup menu shortcut called "ITKTubeTK_CTLungs".

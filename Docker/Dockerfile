# escape= `

FROM microsoft/windowsservercore:1709 AS base

WORKDIR /tmp

RUN powershell (New-Object System.Net.WebClient).DownloadFile('https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe', 'Miniconda3.exe')

RUN powershell Unblock-File Miniconda3.exe

RUN Miniconda3.exe /InstallationType=JustMe /RegisterPython=1 /S /D=C:\Miniconda3

#FROM mcr.microsoft.com/windows/nanoserver:1709

#COPY --from=base C:\Miniconda3 C:\Miniconda3

COPY DLLs C:\Miniconda3\
COPY Lib C:\Miniconda3\

USER ContainerAdministrator
RUN setx /M PATH "%PATH%;C:\Miniconda3;C:\Miniconda3\Scripts;C:\Miniconda3\Library\bin;""
USER ContainerUser
RUN conda install pyqt=5 -y
RUN pip install ruamel.yaml numpy h5py scipy progressbar2 munch pyzmq pyqtgraph requests pyepics pyinstaller ujson

RUN conda install git -y

RUN mkdir Github

ADD SimFrame C:\Github\SimFrame

ADD ASTRA_COMPARISONRunner-HMCC C:\Github\ASTRA_COMPARISONRunner-HMCC

# pyinstaller -F --distpath c:\github\build2\dist --specpath c:\github\build2 --workpath c:\github\build2\build -y  --clean c:\github\ASTRA_COMPARISONRunner-HMCC\mainapp.py

CMD ["powershell"]
git clone https://github.com/VELA-CLARA-software/SimFrame.git
cd SimFrame
git pull
cd ..
git clone https://gitlab.stfc.ac.uk/ujo48515/ASTRA_COMPARISONRunner-HMCC.git
cd ASTRA_COMPARISONRunner-HMCC
git pull
git switch 22_creating_build_docker
git pull
cd ..
docker build --tag nano-server.miniconda:latest .
docker run -it nano-server.miniconda:latest
sudo apt-get update
sudo apt-get install docker-ce
sudo add-apt-repository    "deb [arch=amd64] https://download.docker.com/linux/ubuntu
sudo apt-get install apt-transport-https ca-certificates  curl  software-properties-common
.
end
exit
quit
esc

"
sudo apt-get install apt-transport-https ca-certificates  curl  software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg 
sudo apt-get install docker-ce
apt-cache madison docker-ce
sudo add-apt-repository    "deb [arch=amd64] https://download.docker.com/linux/ubuntu    $(lsb_release -cs)    stable"
apt-cache madison docker-ce
sudo apt-get install docker-ce
sudo add-apt-repository    "deb [arch=amd64] https://download.docker.com/linux/ubuntu    $(lsb_release -cs)    stable"
sudo add-apt-repository    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update
sudo apt-get install docker-ce
sudo curl -L "https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
vi docker-compose.yml

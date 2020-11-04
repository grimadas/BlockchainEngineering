
<!--<p align="center">
  <img width="90%" src="https://github.com/benedekrozemberczki/littleballoffur/blob/master/littleballoffurlogo.jpg?sanitize=true" />
</p>-->

--------------------------------------------------------------------------------

**Blockchain Engineering** is a collection of jupyter notebooks to teach fundamentals of any blockchain system.

Rather than other blockchain courses we follow a different approach we build up blockchain from scratch from bottom to the top. 
The main focus of this notebook is to explain and visually show the "Distribtued systems thinking", and Blokchain architehct thinking in particular.

After this course you will get what is the problems you will solve? What issues you might encounter? Why is it so hard to design a good system? 

The notebooks are build as experiments with a discrete simulation SimPy, this allows you to simulate unreliable communication, malicious behavior and convergence algorithms.   

--------------------------------------------------------------------------------

## Current topics 

* [Distributed systems](https://github.com/grimadas/BlockchainEngineering/blob/master/01_Intro_To_Distribtued_Systems.ipynb). Overlays and communication network. Introduction to simulation framework
* [Gossip](https://github.com/grimadas/BlockchainEngineering/blob/master/02_Gossip_Services.ipynb). Convergence of the transactions, information
* [Faults](https://github.com/grimadas/BlockchainEngineering/blob/master/03_Faults.ipynb) in distributed systems: crashes and disruptions
* [Malicious](https://github.com/grimadas/BlockchainEngineering/blob/master/04_Byzantine.ipynb) nodes, adversary model
* [Consensus](https://github.com/grimadas/BlockchainEngineering/blob/master/05_Consensus.ipynb) and agreement despite malicious nodes

If you notice anything unexpected, or you are want more topics, please open an [issue](https://github.com/grimadas/BlockchainEngineering/issues) and let us know.
If you like the project and want to help us, contributions are very welcome! Feel free to open a [feature request](https://github.com/grimadas/BlockchainEngineering/issues).
We are motivated to constantly make it better.


--------------------------------------------------------------------------------

## Getting started 




1. Clone the repository:

```bash
git clone  https://github.com/grimadas/BlockchainEngineering.git
```

2. Install [python >= 3.7](https://www.python.org/downloads/). Alternatively you can also use [conda](https://anaconda.org). 
3. Install required dependecies 
  
  - To enable some of the animations used install [graphviz](https://www.graphviz.org/download/).
  
  - Install required python dependecies:
  
    ```bash
    pip install -r requirements.txt
    ```
  
4. You can start the exercises by opening the notebooks via: 
  ```bash
   jupyter lab
  ```
  

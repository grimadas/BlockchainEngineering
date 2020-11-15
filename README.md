
<p align="center">
  <img width="90%" src="https://github.com/grimadas/BlockchainEngineering/blob/master/blockhain-engineering-logo.png?sanitize=true" />
</p>

--------------------------------------------------------------------------------

**Blockchain Engineering** is a collection of jupyter notebooks to teach the fundamentals of any blockchain system.

As opposed to other blockchain courses we follow a different approach - we build the blockchain up from scratch, starting from bottom to the top. 
The main focus of this notebook is to explain and visually show how to understand distributed systems and think like a blockchain architect.

At the end of this course you will have a better understanding of the challenges faced while designing a blockchain system and how to overcome them.

The notebooks are built as experiments with a discrete simulation SimPy that allows you to simulate unreliable communication, malicious behavior and convergence algorithms.   

*Start the exercises by forking the repo and go through the notebooks one by one.*

--------------------------------------------------------------------------------

## Topics covered

* [Distributed systems](https://github.com/grimadas/BlockchainEngineering/blob/master/01_Intro_To_Distribtued_Systems.ipynb). Overlays and communication network. Introduction to simulation framework
* [Gossip](https://github.com/grimadas/BlockchainEngineering/blob/master/02_Gossip_Services.ipynb). Convergence of the transactions, information
* [Faults](https://github.com/grimadas/BlockchainEngineering/blob/master/03_Faults.ipynb) in distributed systems: crashes and disruptions
* [Malicious](https://github.com/grimadas/BlockchainEngineering/blob/master/04_Byzantine.ipynb) nodes, adversary model
* [Consensus](https://github.com/grimadas/BlockchainEngineering/blob/master/05_Consensus.ipynb) and agreement despite malicious nodes

If you notice anything unexpected, or you want more topics, please open an [issue](https://github.com/grimadas/BlockchainEngineering/issues) and let us know.
If you like the project and want to help us, contributions are very welcome! Feel free to open a [feature request](https://github.com/grimadas/BlockchainEngineering/issues).
We are motivated to constantly make it better.


--------------------------------------------------------------------------------

## Getting started 




1. Clone/Fork the repository:

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
  
4. You can start the exercises by opening the notebooks via from your cloned directory: 
  ```bash
   jupyter lab
  ```
  

import torch
import pandas as pd
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import torch_geometric.transforms as T
from sklearn.metrics import roc_auc_score, average_precision_score

# Import the registry and the Abstract Base Class from the hidden core
from etl_core.gnn_core import registry, AbstractGNNPipeline

@registry.register("basic_ddi_gnn")
class StudentBasicGNN(AbstractGNNPipeline):
    
    def build_model(self):
        """
        Initialize all PyTorch layers here.
        This function is automatically called during class initialization.
        """
        in_channels = self.config['training'].get('in_channels', -1)
        hidden_channels = self.config['training']['hidden_channels']
        
        # We will use two Graph Convolutional layers
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)

    def data_conversion(self, data: str, ddis: str) -> Data:
        """
        Parse the input CSVs and create a PyTorch Geometric Data object.
        Inputs: 
            data: triples or graps ( for this example we consider only a list of drug ids).
            ddis: the ground truth interactions between drugs.
        """
        print(f"Loading Drugs from {data} and DDIs from {ddis}...")
        
        # 1. Load data
        drugs_df = pd.read_csv(data, header=None, names=['drugbank_id'])
        ddis_df = pd.read_csv(ddis, header=None, names=['drugbank_id_1', 'drugbank_id_2'])
        
        # 2. Create Mappings (CRITICAL if we want to predict on unseen drugs in the future)
        self.drug_to_idx = {drug: idx for idx, drug in enumerate(drugs_df['drugbank_id'])}
        self.idx_to_drug = {idx: drug for drug, idx in self.drug_to_idx.items()}
        
        # 3. Create Node Features (x)
        num_nodes = len(drugs_df)
        # Using Identity Matrix as basic one-hot encoded node features
        x = torch.eye(num_nodes, dtype=torch.float)
        
        # 4. Create Edge Index (edge_index)
        src = [self.drug_to_idx[d] for d in ddis_df['drugbank_id_1']]
        dst = [self.drug_to_idx[d] for d in ddis_df['drugbank_id_2']]
        edge_index = torch.tensor([src, dst], dtype=torch.long)
        
        return Data(x=x, edge_index=edge_index)

    def data_split(self, data: Data):
        """
        Split the graph into Training, Validation, and Test sets.
        Ensure negative samples are generated for the link prediction task.
        """
        transform = T.RandomLinkSplit(
            num_val=self.config['training'].get('val_ratio', 0.1),
            num_test=self.config['training'].get('test_ratio', 0.1),
            is_undirected=True,
            add_negative_train_samples=True,
            neg_sampling_ratio=1.0
        )
        train_data, val_data, test_data = transform(data)
        return train_data, val_data, test_data

    def forward(self, x, edge_index, edge_label_index):
        """
        Implement the forward pass.
        - x & edge_index are used to generate node embeddings (Encoding).
        - edge_label_index defines the specific pairs to predict (Decoding).
        """
        # Encode
        z = self.conv1(x, edge_index).relu()
        z = self.conv2(z, edge_index)
        
        # Decode using dot product of source and target embeddings
        src_emb = z[edge_label_index[0]]
        dst_emb = z[edge_label_index[1]]
        
        # Return raw logits (Do not apply sigmoid here, BCEWithLogitsLoss handles it)
        return (src_emb * dst_emb).sum(dim=-1)

    def train_model(self, train_data, val_data):
        """
        Implement a basic training loop (without early stopping).
        """
        optimizer = torch.optim.Adam(self.parameters(), lr=self.config['training']['learning_rate'])
        criterion = torch.nn.BCEWithLogitsLoss()
        
        epochs = self.config['training']['epochs']
        
        for epoch in range(1, epochs + 1):
            self.train()
            optimizer.zero_grad()
            
            # self() calls the forward method of this class
            logits = self(train_data.x, train_data.edge_index, train_data.edge_label_index)
            loss = criterion(logits, train_data.edge_label.float())
            
            loss.backward()
            optimizer.step()
            
            # Optional: Calculate validation loss just for terminal output
            self.eval()
            with torch.no_grad():
                val_logits = self(val_data.x, val_data.edge_index, val_data.edge_label_index)
                val_loss = criterion(val_logits, val_data.edge_label.float()).item()
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch:03d} | Train Loss: {loss.item():.4f} | Val Loss: {val_loss:.4f}")

    def evaluate_model(self, test_data):
        """
        Evaluate the trained model on the test set and return metrics.
        Returns a dictionary with metric names as keys.
        """
        self.eval()
        with torch.no_grad():
            logits = self(test_data.x, test_data.edge_index, test_data.edge_label_index)
            # Apply sigmoid to convert raw logits to probabilities
            probs = torch.sigmoid(logits)
            
        y_true = test_data.edge_label.cpu().numpy()
        y_pred = probs.cpu().numpy()
        
        return {
            "ROC_AUC": float(roc_auc_score(y_true, y_pred)),
            "Average_Precision": float(average_precision_score(y_true, y_pred))
        }


@registry.register("my_ggn_model")
class MyGGNModel(AbstractGNNPipeline):
    
    def build_model(self):
        """
        Initialize all PyTorch layers here.        
        Inputs:
        - self: Allows access to hyperparameters using self.config['training']
        """
        in_channels = self.config['training'].get('in_channels', -1)
        hidden_channels = self.config['training']['hidden_channels']

        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.conv3 = GCNConv(hidden_channels, hidden_channels)
        self.dropout = torch.nn.Dropout(p=0.3)

    def data_conversion(self, data: str, ddis: str) -> Data:
        """
        Parse the input files and create a PyTorch Geometric Data object.
        
        Inputs:
        - data (str): Filepath to the TTL file that contains your graph.
        - ddis (str): Filepath to the ddis (the ground truth of drug interactions) file.
        
        CRITICAL: You must populate two dictionaries for the system to evaluate unseen pairs:
        - self.drug_to_idx = { "DRUG_ID": integer_node_index }
        - self.idx_to_drug = { integer_node_index: "DRUG_ID" }
        """
        from rdflib import Graph as RDFGraph

        print(f"Loading TTL graph from {data} and DDIs from {ddis}...")

        drugs_df = pd.read_csv("data/drugs.csv", header=None, names=['drugbank_id'])
        ddis_df = pd.read_csv(ddis, header=None, names=['drugbank_id_1', 'drugbank_id_2'])

        self.drug_to_idx = {drug: idx for idx, drug in enumerate(drugs_df['drugbank_id'])}
        self.idx_to_drug = {idx: drug for drug, idx in self.drug_to_idx.items()}

        num_nodes = len(drugs_df)
        x = torch.eye(num_nodes, dtype=torch.float)

        src = [self.drug_to_idx[d] for d in ddis_df['drugbank_id_1'] if d in self.drug_to_idx]
        dst = [self.drug_to_idx[d] for d in ddis_df['drugbank_id_2'] if d in self.drug_to_idx]
        edge_index = torch.tensor([src, dst], dtype=torch.long)

        g = RDFGraph()
        g.parse(data, format="turtle")

        extra_src = []
        extra_dst = []

        sparql_query = """
        PREFIX ex: <http://example.org/drugkg/>
        SELECT ?d1 ?d2 WHERE {
            ?d1 ex:hasTarget ?protein .
            ?d2 ex:hasTarget ?protein .
            FILTER(?d1 != ?d2)
        }
        """
        results = g.query(sparql_query)
        for row in results:
            d1 = str(row.d1).split("/")[-1]
            d2 = str(row.d2).split("/")[-1]
            if d1 in self.drug_to_idx and d2 in self.drug_to_idx:
                extra_src.append(self.drug_to_idx[d1])
                extra_dst.append(self.drug_to_idx[d2])

        if extra_src:
            extra_edge_index = torch.tensor([extra_src, extra_dst], dtype=torch.long)
            edge_index = torch.cat([edge_index, extra_edge_index], dim=1)

        return Data(x=x, edge_index=edge_index)

    def data_split(self, data: Data):
        """
        Split the graph into Training, Validation, and Test sets.
        
        Inputs:
        - data (Data): The PyTorch Geometric Data object returned by data_conversion().
        """
        transform = T.RandomLinkSplit(
            num_val=self.config['training'].get('val_ratio', 0.1),
            num_test=self.config['training'].get('test_ratio', 0.1),
            is_undirected=True,
            add_negative_train_samples=True,
            neg_sampling_ratio=1.0
        )
        train_data, val_data, test_data = transform(data)
        return train_data, val_data, test_data

    def forward(self, x, edge_index, edge_label_index):
        """
        Implement the forward pass.
        
        Inputs:
        - x (Tensor): Node feature matrix. Used to generate node embeddings (Encoding).
        - edge_index (Tensor): Graph connectivity (edges) for message passing.
        - edge_label_index (Tensor): Defines the specific pairs to predict (Decoding).
        """
        z = self.conv1(x, edge_index).relu()
        z = self.dropout(z)
        z = self.conv2(z, edge_index).relu()
        z = self.dropout(z)
        z = self.conv3(z, edge_index)

        src_emb = z[edge_label_index[0]]
        dst_emb = z[edge_label_index[1]]

        return (src_emb * dst_emb).sum(dim=-1)

    def train_model(self, train_data, val_data):
        """
        Implement the training loop.
        Calculate the loss and update the model parameters.
        
        Inputs:
        - train_data (Data): Graph split containing the training edges and labels.
        - val_data (Data): Graph split containing the validation edges and labels.
        """
        optimizer = torch.optim.Adam(self.parameters(), lr=self.config['training']['learning_rate'])
        criterion = torch.nn.BCEWithLogitsLoss()
        epochs = self.config['training']['epochs']

        for epoch in range(1, epochs + 1):
            self.train()
            optimizer.zero_grad()
            logits = self(train_data.x, train_data.edge_index, train_data.edge_label_index)
            loss = criterion(logits, train_data.edge_label.float())
            loss.backward()
            optimizer.step()

            self.eval()
            with torch.no_grad():
                val_logits = self(val_data.x, val_data.edge_index, val_data.edge_label_index)
                val_loss = criterion(val_logits, val_data.edge_label.float()).item()

            if epoch % 10 == 0:
                print(f"Epoch {epoch:03d} | Train Loss: {loss.item():.4f} | Val Loss: {val_loss:.4f}")
    def evaluate_model(self, test_data):
        """
        Evaluate the trained model on the test set and return metrics.
        Must return a dictionary, e.g., {"ROC_AUC": 0.85, "Average_Precision": 0.82}
        
        Inputs:
        - test_data (Data): Graph split containing the test edges and labels.
        """
        self.eval()
        with torch.no_grad():
            logits = self(test_data.x, test_data.edge_index, test_data.edge_label_index)
            probs = torch.sigmoid(logits)

        y_true = test_data.edge_label.cpu().numpy()
        y_pred = probs.cpu().numpy()

        return {
            "ROC_AUC": float(roc_auc_score(y_true, y_pred)),
            "Average_Precision": float(average_precision_score(y_true, y_pred))
        }
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import TransformerEncoder, TransformerEncoderLayer

class QuoridorNNet(nn.Module):
    """
    Input: slen - integer representing the length of the sequence run through transformer
           ntoken - integer representing the amount of total tokens
           d_model - MUST BE EVEN, represents the dimension of the model
           ninp - integer representing number of input layers
           nhead - integer representing the number of heads in the multiheadattention models
           nhid - integer representing the dimension of the feedforward network model in nn.TransformerEncoder
           nlayers - integer representing the number of nn.TransformerEncoderLayer in nn.TransformerEncoder
           dropout - integer representing the dropout percentage you want to use (Default=0.5) [OPTIONAL]
    Description: Initailize transormer model class creating the appropiate layers
    Output: None
    """
    def __init__(self, game, nwalltoken: int = 3, npawntoken: int = 3, d_model: int = 200,
                 nhead: int = 2, d_hid: int = 2048, nlayers: int = 2, dropout: float = 0.5, ):
        # game params
        self.action_size = game.getActionSize()
        self.input_size = game.getBoardSize()
        
        super().__init__()
        self.model_type = 'Transformer'
        self.embeddingSquares = nn.Embedding(nwalltoken, int(d_model / 2))
        self.embeddingWalls = nn.Embedding(npawntoken, int(d_model / 2))
        self.embeddingRemWalls = nn.Embedding(11, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        encoder_layers = TransformerEncoderLayer(d_model, nhead, d_hid, dropout, batch_first=True)
        self.transformer_encoder = TransformerEncoder(encoder_layers, nlayers)
        self.d_model = d_model
        self.softmax = nn.Softmax(dim=1) #Softmax activation layer
        self.gelu = nn.GELU() #GELU activation layer
        self.flatten = nn.Flatten(start_dim=1) #Flatten layer
        self.decoder = nn.Linear(d_model,1) #Decode layer
        self.v_output = nn.Linear(83, 1) #Decode layer
        self.p_output = nn.Linear(83, self.action_size) #Decode layer

        self.init_weights()

    def init_weights(self) -> None:
        initrange = 0.1
        self.embeddingSquares.weight.data.uniform_(-initrange, initrange)
        self.embeddingWalls.weight.data.uniform_(-initrange, initrange)
        self.embeddingRemWalls.weight.data.uniform_(-initrange, initrange)
        self.decoder.bias.data.zero_()
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def forward(self, src):
        """
        Arguments:
            src: Tensor, shape [batch_size, 2+81+64]

        Returns:
            output Tensor of shape ````
        """
        srcRemWalls = src[:,:2].int()
        srcRemWalls = self.embeddingRemWalls(srcRemWalls)           # batch_size x 2 x d_model
        srcSquares = src[:,2: 2 + 81].int()  
        srcSquares = self.embeddingSquares(srcSquares)          # batch_size x 81 x d_model/2
        srcWalls = src[:, 2 + 81:].int()  
        srcWalls = self.embeddingWalls(srcWalls)                # batch_size x 81 x d_model/2
        src = torch.cat((srcSquares, srcWalls), dim=2)          # batch_size x 81 x d_model
        src = torch.cat((srcRemWalls, src), dim=1)              # batch_size x 83 x d_model
        src = src * math.sqrt(self.d_model)                     # batch_size x 83 x d_model
        src = self.pos_encoder(src)                             # batch_size x 83 x d_model
        output = self.transformer_encoder(src)                  # batch_size x 83 x d_model
        output = self.gelu(output)                               
        output = self.decoder(output)                           # batch_size x 83 x 1
        output = self.gelu(output)
        output = self.flatten(output)                           # batch_size x 83
        v = self.v_output(output)                               # batch_size x 1
        v = self.softmax(v) #Get softmax probability
        p = self.p_output(output)                               # batch_size x action_size
        p = self.softmax(p) #Get softmax probability
        
        return p,v
    
class PositionalEncoding(nn.Module):
    """
    Input: d_model - integer containing the size of the data model input
           dropout - integer representing the dropout percentage you want to use (Default=0.1) [OPTIONAL]
           max_len - integer representing the max amount of tokens in a input (Default=5000) [OPTIONAL]
    Description: Initailize positional encoding layer
    Output: None
    """
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    """
    Input: x - pytorch tensor containing the input data for the model (seq_len,batch,d_model)
    Description: forward pass of the positional encoding layer
    Output: pytorch tensor containing positional encoded data (floats)
    """
    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)
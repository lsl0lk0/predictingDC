# region import
from prepare_data import PROTACSet
from model import GraphConv, SmilesNet, Classifier
from train_and_test import train, valid
import torch
import torch.nn as nn
import pickle
from torch.utils.tensorboard import SummaryWriter
from torch.utils.data import DataLoader
import numpy as np
import random
import os
# endregion
# torch.cuda.empty_cache()


Random_seeds = [1234, 6290, 6425, 9023, 3634, 7151, 7868, 2824]
SEED = Random_seeds[7]
print('Seed is %d' % SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic=True
torch.backends.cudnn.benchmark = False
random.seed(SEED)
np.random.seed(SEED)

writer = SummaryWriter()
LEARNING_RATE = 0.0001
BATCH_SIZE = 1
EPOCH = 400
TRAIN_SIZE = 1972
VALID_SIZE = 2218

MODEL_NAME = 'final_e%d_s%d' % (EPOCH, SEED)
VAL_INTERVAL = 2
SMILES_CHAR =['?','C', '(', '=', 'O', ')', 'N', '[', '@', 'H', ']', '1', 'c', 'n', '/', '2', '#', 'S', 's', '+', '-', '\\', '3', '4', 'l', 'F', 'o', 'I', 'B', 'r', 'P', '5', '6', 'i', '7', '8', '9', '%', '0', 'p']

def trans_smiles(x):
    temp = list(x)
    temp = [SMILES_CHAR.index(i) if i in SMILES_CHAR else 0 for i in temp]
    return temp

def read_pkl(path):
    with open(path,'rb') as f:
        pkl_content = pickle.load(f)
    return pkl_content

def main():
    name_list = read_pkl('data/name.pkl')
    smiles_dict = read_pkl('data/smiles.pkl')
    target_atom_dict = read_pkl('data/target_atom.pkl')
    target_bond_dict = read_pkl('data/target_bond.pkl')
    ligase_atom_dict = read_pkl('data/ligase_atom.pkl')
    ligase_bond_dict = read_pkl('data/ligase_bond.pkl')
    target_ligand_atom_dict = read_pkl('data/target_ligand_atom.pkl')
    target_ligand_bond_dict = read_pkl('data/target_ligand_bond.pkl')
    ligase_ligand_atom_dict = read_pkl('data/ligase_ligand_atom.pkl')
    ligase_ligand_bond_dict = read_pkl('data/ligase_ligand_bond.pkl')
    label_dict = read_pkl('data/label.pkl')

    smiles = [trans_smiles(smiles_dict[x]) for x in name_list]
    target_atom = [target_atom_dict[x] for x in name_list]
    target_bond = [target_bond_dict[x] for x in name_list]
    ligase_atom = [ligase_atom_dict[x] for x in name_list]
    ligase_bond = [ligase_bond_dict[x] for x in name_list]
    target_ligand_atom = [target_ligand_atom_dict[x] for x in name_list]
    target_ligand_bond = [target_ligand_bond_dict[x] for x in name_list]
    ligase_ligand_atom = [ligase_ligand_atom_dict[x] for x in name_list]
    ligase_ligand_bond = [ligase_ligand_bond_dict[x] for x in name_list]
    label = [label_dict[x] for x in name_list]

    train_data = PROTACSet(ligase_atom[:TRAIN_SIZE], ligase_bond[:TRAIN_SIZE],
                           target_atom[:TRAIN_SIZE], target_bond[:TRAIN_SIZE],
                           ligase_ligand_atom[:TRAIN_SIZE], ligase_ligand_bond[:TRAIN_SIZE],
                           target_ligand_atom[:TRAIN_SIZE], target_ligand_bond[:TRAIN_SIZE],
                           smiles[:TRAIN_SIZE], label[:TRAIN_SIZE])
    valid_data = PROTACSet(ligase_atom[TRAIN_SIZE:], ligase_bond[TRAIN_SIZE:],
                           target_atom[TRAIN_SIZE:], target_bond[TRAIN_SIZE:],
                           ligase_ligand_atom[TRAIN_SIZE:], ligase_ligand_bond[TRAIN_SIZE:],
                           target_ligand_atom[TRAIN_SIZE:], target_ligand_bond[TRAIN_SIZE:],
                           smiles[TRAIN_SIZE:], label[TRAIN_SIZE:])
    test_data = PROTACSet(ligase_atom[TRAIN_SIZE:], ligase_bond[TRAIN_SIZE:],
                          target_atom[TRAIN_SIZE:], target_bond[TRAIN_SIZE:],
                          ligase_ligand_atom[TRAIN_SIZE:], ligase_ligand_bond[TRAIN_SIZE:],
                          target_ligand_atom[TRAIN_SIZE:], target_ligand_bond[TRAIN_SIZE:],
                          smiles[TRAIN_SIZE:], label[TRAIN_SIZE:])

    train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
    valid_loader = DataLoader(valid_data, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_data, batch_size=BATCH_SIZE, shuffle=False)

    ligase_model = GraphConv(num_embeddings=5)
    target_model = GraphConv(num_embeddings=5)
    ligase_ligand_model = GraphConv(num_embeddings=10)
    target_ligand_model = GraphConv(num_embeddings=10)
    smiles_model = SmilesNet()
    model = Classifier(ligase_model, target_model, ligase_ligand_model, target_ligand_model, smiles_model)
    # device = torch.device('cpu')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    model = train(model, LEARNING_RATE, EPOCH, train_loader, valid_loader, device, writer, MODEL_NAME, VAL_INTERVAL)
    torch.save(model,'model_%s.pth' % MODEL_NAME)
    loss_test, acc_test = valid(model, test_loader, device)
    print('Test with loss: %.4f, accuracy: %.4f' % (loss_test, acc_test))

if __name__== '__main__':
    main()
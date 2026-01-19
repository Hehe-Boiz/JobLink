import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Modal, FlatList, StyleSheet, Platform } from 'react-native';
import { TextInput, IconButton, Divider, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

const AppSelector = ({ label, placeholder, data, selectedValue, onSelect, required = false }) => {
  const [visible, setVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const theme = useTheme()


  const filteredData = data.filter(item => 
    item.name.toLowerCase().includes(searchText.toLowerCase())
  );


  const selectedItemName = data.find(item => item.id === selectedValue?.id)?.name;

  const handleSelect = (item) => {
    onSelect(item);
    setVisible(false);
    setSearchText('');
  };

  return (
    <View style={styles.container}>

      {label && (
        <Text style={styles.label}>
          {label} {required && <Text style={{ color: 'red' }}>*</Text>}
        </Text>
      )}

      <TouchableOpacity 
        style={styles.selectorBox} 
        onPress={() => setVisible(true)}
        activeOpacity={0.7}
      >
        <Text style={[styles.valueText, !selectedValue && styles.placeholder]}>
          {selectedItemName || placeholder || "Chạm để chọn..."}
        </Text>
        <MaterialCommunityIcons name="chevron-down" size={24} color="#AAA6B9" />
      </TouchableOpacity>

      <Modal visible={visible} animationType="slide" onRequestClose={() => setVisible(false)}>
        <SafeAreaView style={styles.modalContainer}>
          

          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setVisible(false)}>
               <MaterialCommunityIcons name="close" size={28} color="#130160" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Chọn {label}</Text>
            <View style={{ width: 28 }} />
          </View>

          <View style={styles.searchContainer}>
            <TextInput
              mode="outlined"
              placeholder="Tìm kiếm..."
              value={searchText}
              onChangeText={setSearchText}
              style={styles.searchInput}
              outlineColor="#EAEAEA"
              activeOutlineColor="#130160"
              left={<TextInput.Icon icon="magnify" color="#AAA6B9" />}
              theme={{ roundness: 10 }}
            />
          </View>

          <FlatList
            data={filteredData}
            keyExtractor={(item) => item.id.toString()}
            contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 20 }}
            renderItem={({ item }) => {
              const isSelected = selectedValue?.id === item.id;
              return (
                <TouchableOpacity 
                  style={[styles.item, isSelected && styles.itemSelected]} 
                  onPress={() => handleSelect(item)}
                >
                  <Text style={[styles.itemText, isSelected && styles.itemTextSelected]}>
                    {item.name}
                  </Text>
                  {isSelected && <MaterialCommunityIcons name="check" size={20} color="#130160" />}
                </TouchableOpacity>
              );
            }}
            ItemSeparatorComponent={() => <Divider />}
            ListEmptyComponent={
                <Text style={styles.emptyText}>Không tìm thấy kết quả.</Text>
            }
          />
        </SafeAreaView>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 15,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#524B6B',
    marginBottom: 8,
  },
  selectorBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#EAEAEA',
    borderRadius: 10,
    height: 50, 
    paddingHorizontal: 15,
  },
  valueText: {
    fontSize: 14,
    color: '#130160',
  },
  placeholder: {
    color: '#AAA6B9',
  },
  
 
  modalContainer: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#130160',
  },
  searchContainer: {
    padding: 20,
  },
  searchInput: {
    backgroundColor: 'white',
    height: 45,
    fontSize: 14,
  },
  item: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
  },
  itemSelected: {
    backgroundColor: '#F3F0FF',
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  itemText: {
    fontSize: 16,
    color: '#524B6B',
  },
  itemTextSelected: {
    color: '#130160',
    fontWeight: 'bold',
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    marginTop: 20,
  }
});

export default AppSelector;
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

const AppHeader = ({ title, showBack = true, rightIcon, onRightPress }) => {
  const navigation = useNavigation();

  return (
    <View style={styles.header}>

      {showBack ? (
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.iconBtn}>
          <MaterialCommunityIcons name="arrow-left" size={24} color="#130160" />
        </TouchableOpacity>
      ) : (
        <View style={styles.placeholder} />
      )}


      <Text style={styles.title}>{title}</Text>

      {rightIcon ? (
        <TouchableOpacity onPress={onRightPress} style={styles.iconBtn}>
          <MaterialCommunityIcons name={rightIcon} size={24} color="#FF9228" />
        </TouchableOpacity>
      ) : (
        <View style={styles.placeholder} />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  header: {
    height: 60,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
    elevation: 2,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#130160',
  },
  iconBtn: {
    padding: 5,
  },
  placeholder: {
    width: 34,
  }
});

export default AppHeader;
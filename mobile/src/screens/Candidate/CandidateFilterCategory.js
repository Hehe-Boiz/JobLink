import React, { useState } from 'react';
import { View, StyleSheet, TextInput, TouchableOpacity, FlatList} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import CustomText from '../../components/CustomText';
import CustomHeader from '../../components/CustomHeader';
import styles from '../../styles/Candidate/CandidateFilterCategoryStyles'

const DATA = [
    { id: '1', title: 'Design', count: 140, icon: 'briefcase-edit-outline' },
    { id: '2', title: 'Finance', count: 250, icon: 'wallet-outline' },
    { id: '3', title: 'Education', count: 120, icon: 'school-outline' },
    { id: '4', title: 'Restaurant', count: 85, icon: 'silverware-fork-knife' },
    { id: '5', title: 'Health', count: 235, icon: 'heart-pulse' },
    { id: '6', title: 'Programmer', count: 412, icon: 'monitor-cellphone' },
];

const CandidateFilterCategory = ({ navigation }) => {
    const [selectedId, setSelectedId] = useState('1');
    const [searchText, setSearchText] = useState('');

    const renderItem = ({ item }) => {
        const isSelected = selectedId === item.id;

        const cardBg = isSelected ? '#FCA34D' : '#FFFFFF';
        const titleColor = isSelected ? '#FFFFFF' : '#130160';
        const subtitleColor = isSelected ? '#FFFFFF' : '#524B6B';
        const circleBg = isSelected ? 'rgba(255, 255, 255, 0.2)' : '#FFF4E5'; // Light orange circle for unselected
        const iconColor = isSelected ? '#FFFFFF' : '#FF9228';

        let customCircleBg = circleBg;
        let customIconColor = iconColor;

        if (!isSelected) {
            customCircleBg = '#FFF4E5';
            customIconColor = '#FF9228';
        }

        return (
            <TouchableOpacity
                style={[styles.card, { backgroundColor: cardBg }]}
                onPress={() => setSelectedId(item.id)}
                activeOpacity={0.8}
            >
                <View style={[styles.iconCircle, { backgroundColor: isSelected ? '#FFFFFF' : '#FFF4E5' }]}>
                    <MaterialCommunityIcons
                        name={item.icon}
                        size={30}
                        color={isSelected ? '#FCA34D' : '#FCA34D'}
                    />
                </View>
                <CustomText style={[styles.cardTitle, { color: titleColor }]}>
                    {item.title}
                </CustomText>
                <CustomText style={[styles.cardCount, { color: subtitleColor }]}>
                    {item.count} Jobs
                </CustomText>
            </TouchableOpacity>
        );
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <CustomHeader navigation={navigation} showMenu={false} />

            <View style={styles.content}>

                <View style={styles.searchContainer}>
                    <View style={styles.searchWrapper}>
                        <MaterialCommunityIcons name="magnify" size={24} color="#AAA6B9" style={styles.searchIcon} />
                        <TextInput
                            style={styles.searchInput}
                            placeholder="Search"
                            placeholderTextColor="#AAA6B9"
                            value={searchText}
                            onChangeText={setSearchText}
                        />
                    </View>
                    <TouchableOpacity style={styles.filterBtn}>
                         <MaterialCommunityIcons name="tune-variant" size={24} color="#FFFFFF" />
                    </TouchableOpacity>
                </View>

                <CustomText style={styles.screenTitle}>Specialization</CustomText>

                <FlatList
                    data={DATA}
                    renderItem={renderItem}
                    keyExtractor={(item) => item.id}
                    numColumns={2}
                    showsVerticalScrollIndicator={false}
                    columnWrapperStyle={styles.columnWrapper}
                    contentContainerStyle={styles.listContainer}
                />
            </View>
        </SafeAreaView>
    );
};

export default CandidateFilterCategory;
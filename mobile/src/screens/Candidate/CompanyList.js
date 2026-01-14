import React, {useState} from 'react';
import {View, FlatList, TextInput, TouchableOpacity} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomHeader from '../../components/common/CustomHeader'; //
import CompanyCard from '../../components/Candidate/CompanyCard';
import styles from '../../styles/Candidate/CompanyListStyles';

const MOCK_COMPANIES = [
    {
        id: '1',
        name: 'Google Inc',
        followers: '1M',

        logo: 'https://cdn-icons-png.flaticon.com/512/300/300221.png',
        bg: '#F4F8FF'
    },
    {
        id: '2',
        name: 'Dribbble Inc',
        followers: '1M',
        logo: 'https://cdn-icons-png.flaticon.com/512/2111/2111370.png',
        bg: '#FFF0F5'
    },
    {
        id: '3',
        name: 'Twitter Inc',
        followers: '1M',
        logo: 'https://cdn-icons-png.flaticon.com/512/3670/3670151.png',
        bg: '#F0F8FF'
    },
    {
        id: '4',
        name: 'Apple Inc',
        followers: '1M',
        logo: 'https://cdn-icons-png.flaticon.com/512/0/747.png',
        bg: '#F5F5F5'
    },
    {
        id: '5',
        name: 'Facebook Inc',
        followers: '1M',
        logo: 'https://cdn-icons-png.flaticon.com/512/5968/5968764.png',
        bg: '#F0F6FF'
    },
    {
        id: '6',
        name: 'Microsoft Inc',
        followers: '1M',
        logo: 'https://cdn-icons-png.flaticon.com/512/732/732221.png',
        bg: '#F3F9FF'
    },
];


const CompanyList = ({navigation}) => {
    const [searchText, setSearchText] = useState('');
    const [data, setData] = useState(MOCK_COMPANIES);

    const handleSearch = (text) => {
        setSearchText(text);
        if (text) {
            const filtered = MOCK_COMPANIES.filter(item =>
                item.name.toLowerCase().includes(text.toLowerCase())
            );
            setData(filtered);
        } else {
            setData(MOCK_COMPANIES);
        }
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>

            <View style={styles.searchContainer}>
                <View style={styles.searchBar}>
                    <MaterialCommunityIcons name="magnify" size={24} color="#AAA6B9"/>
                    <TextInput
                        style={styles.searchInput}
                        placeholder="Search Company..."
                        value={searchText}
                        onChangeText={handleSearch}
                    />
                </View>
            </View>

            <FlatList
                data={data}
                keyExtractor={(item) => item.id}
                numColumns={2}
                columnWrapperStyle={styles.columnWrapper}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
                renderItem={({item}) => (
                    <CompanyCard item={item}/>
                )}
            />
        </SafeAreaView>
    );
};

export default CompanyList;
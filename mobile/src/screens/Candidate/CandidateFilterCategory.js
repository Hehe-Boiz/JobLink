import React, {useState, useMemo} from 'react';
import {View, TextInput, TouchableOpacity, ScrollView, StyleSheet, Alert} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import CustomHeader from '../../components/common/CustomHeader';
import styles from '../../styles/Candidate/CandidateFilterCategoryStyles';
import CustomFooter from "../../components/common/CustomFooter";

const RANDOM_ICONS = [
    'briefcase-edit-outline', 'wallet-outline', 'school-outline',
    'silverware-fork-knife', 'heart-pulse', 'monitor-cellphone',
    'camera-outline', 'car-outline', 'coffee-outline'
];

const CandidateFilterCategory = ({navigation, route}) => {
    const {categories} = route?.params || {categories: []};

    const [selectedId, setSelectedId] = useState(null);
    const [searchText, setSearchText] = useState('');

    const processedData = useMemo(() => {
        return categories.map((cat, index) => ({
            id: cat.id,
            title: cat.name,
            count: Math.floor(Math.random() * 490) + 10,
            icon: RANDOM_ICONS[index % RANDOM_ICONS.length]
        }));
    }, [categories]);

    const filteredData = useMemo(() => {
        return processedData.filter(item =>
            item.title?.toLowerCase().includes(searchText.toLowerCase())
        );
    }, [searchText, processedData]);

    const handleApply = () => {
        if (!selectedId) {
            Alert.alert("Thông báo", "Vui lòng chọn một danh mục trước.");
            return;
        }

        const selectedCategory = processedData.find(item => item.id === selectedId);

        if (selectedCategory) {
            const filterParams = {
                category: {
                    id: selectedCategory.id,
                    name: selectedCategory.title
                }
            };

            console.log("Applying Category Filter:", filterParams);

            navigation.navigate('CandidateSearchResults', {filterParams});
        }
    };

    const handleSelect = (id) => {
        setSelectedId(id);
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <CustomHeader navigation={navigation} showMenu={false}/>

            <View style={styles.content}>
                <View style={styles.searchContainer}>
                    <View style={styles.searchWrapper}>
                        <MaterialCommunityIcons name="magnify" size={24} color="#AAA6B9" style={styles.searchIcon}/>
                        <TextInput
                            style={styles.searchInput}
                            placeholder="Search"
                            placeholderTextColor="#AAA6B9"
                            value={searchText}
                            onChangeText={setSearchText}
                        />
                    </View>
                    <TouchableOpacity style={styles.filterBtn} onPress={() => navigation.navigate('CandidateSearchAdvance')}>
                        <MaterialCommunityIcons name="tune-variant" size={24} color="#FFFFFF"/>
                    </TouchableOpacity>
                </View>

                <CustomText style={styles.screenTitle}>Specialization</CustomText>

                <ScrollView
                    showsVerticalScrollIndicator={false}
                    contentContainerStyle={{paddingBottom: 150, paddingTop: 30}}
                >
                    <View style={{
                        flexDirection: 'row',
                        flexWrap: 'wrap',
                        justifyContent: 'space-between',
                        paddingHorizontal: 10,
                    }}>
                        {filteredData.length > 0 ? (
                            filteredData.map((item) => {
                                const isSelected = selectedId === item.id;
                                // Theme màu sắc
                                const theme = {
                                    cardBg: isSelected ? '#FCA34D' : '#FFFFFF',
                                    titleColor: isSelected ? '#FFFFFF' : '#130160',
                                    subtitleColor: isSelected ? '#FFFFFF' : '#524B6B',
                                    iconCircleBg: isSelected ? '#FFFFFF' : '#FFF4E5',
                                    iconColor: '#FCA34D',
                                };

                                return (
                                    <TouchableOpacity
                                        key={item.id}
                                        style={[
                                            styles.card,
                                            {
                                                backgroundColor: theme.cardBg,
                                                width: '48%',
                                                marginBottom: 15,
                                            }
                                        ]}
                                        onPress={() => handleSelect(item.id)}
                                        activeOpacity={0.8}
                                    >
                                        <View style={[styles.iconCircle, {backgroundColor: theme.iconCircleBg}]}>
                                            <MaterialCommunityIcons
                                                name={item.icon}
                                                size={30}
                                                color={theme.iconColor}
                                            />
                                        </View>
                                        <CustomText style={[styles.cardTitle, {color: theme.titleColor}]}>
                                            {item.title}
                                        </CustomText>
                                        <CustomText style={[styles.cardCount, {color: theme.subtitleColor}]}>
                                            {item.count} Jobs
                                        </CustomText>
                                    </TouchableOpacity>
                                );
                            })
                        ) : (
                            <View style={{width: '100%', alignItems: 'center', marginTop: 20}}>
                                <CustomText>No category found</CustomText>
                            </View>
                        )}
                    </View>
                </ScrollView>
            </View>
            <CustomFooter
                applyTitle="APPLY NOW"
                onApply={handleApply}
            />
        </SafeAreaView>
    );
};

export default CandidateFilterCategory;
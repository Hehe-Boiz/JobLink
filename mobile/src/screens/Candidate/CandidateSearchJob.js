import React, {useState} from "react";
import {SafeAreaView} from "react-native-safe-area-context";
import {View, StyleSheet, TextInput, TouchableOpacity, ScrollView, FlatList} from "react-native";
import BgHeader from '../../../assets/images/Background.svg'
import CustomHeader from "../../components/CustomHeader";
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from "../../components/CustomText";
import JobCard from "../../components/Candidate/JobCard";
import MyStyles from "../../styles/MyStyles";
import styles from '../../styles/Candidate/CandidateSearchJobStyles'

const MOCK_RESULTS = [
    {
        id: '1',
        title: 'UI/UX Designer',
        company: 'Google inc',
        location: 'California, USA',
        salary: '$15K',
        posted: '25 minute ago',
        logo: 'https://cdn-icons-png.flaticon.com/512/2991/2991148.png',
        tags: ['Design', 'Full time', 'Senior designer']
    },
    {
        id: '2',
        title: 'Lead Designer',
        company: 'Dribbble inc',
        location: 'California, USA',
        salary: '$20K',
        posted: '25 minute ago',
        logo: 'https://cdn-icons-png.flaticon.com/512/2111/2111370.png',
        tags: ['Design', 'Full time', 'Senior designer']
    }
];

const CandidateSearchJob = ({navigation}) => {
    const [search, setSearch] = useState('Design');
    const [location, setLocation] = useState('California, USA');

    return (

        <View style={styles.container}>
            <View style={styles.headerContainer}>
                <BgHeader
                    width="100%"
                    height="350"
                    style={styles.bg}
                    preserveAspectRatio="none"
                />

                <SafeAreaView edges={['top']}>
                    <CustomHeader navigation={navigation} iconColor="white" showMenu={false}/>

                    <View style={styles.searchContent}>
                        <View style={styles.searchBoxContainer}>
                            <View style={styles.inputWrapper}>
                                <MaterialCommunityIcons name="magnify" size={20} color="#AAA6B9"/>
                                <TextInput
                                    style={styles.textInput}
                                    value={search}
                                    onChangeText={setSearch}
                                    placeholder="Design"
                                    placeholderTextColor="#AAA6B9"

                                />
                            </View>
                            <View style={styles.inputWrapper}>
                                <MaterialCommunityIcons name="map-marker-outline" size={20} color="#FF9228"/>
                                <TextInput
                                    style={styles.textInput}
                                    value={location}
                                    onChangeText={setLocation}
                                    placeholder="Location"
                                    placeholderTextColor="#AAA6B9"
                                />
                            </View>
                        </View>
                    </View>
                </SafeAreaView>
            </View>
            <View style={[styles.filterBar, MyStyles.mb4]}>
                <TouchableOpacity style={styles.filterIconBtn}>
                    <MaterialCommunityIcons name="tune-variant" size={20} color="white"/>
                </TouchableOpacity>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipScroll}>
                    {['Senior designer', 'Designer', 'Full-time', 'Remote'].map((filter, index) => (
                        <TouchableOpacity key={index} style={styles.chipBtn}>
                            <CustomText style={styles.chipText}>{filter}</CustomText>
                        </TouchableOpacity>
                    ))}
                </ScrollView>
            </View>
            <FlatList
                data={MOCK_RESULTS}
                renderItem={({item}) => <JobCard item={item} variant="search"/>}
                keyExtractor={item => item.id}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
            />
        </View>
    );
};

export default CandidateSearchJob;


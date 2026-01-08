import React, {useState, useEffect} from 'react';
import {View, TextInput, FlatList, Image, TouchableOpacity} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomHeader from '../../components/common/CustomHeader';
import CustomText from '../../components/common/CustomText';
import JobCard from '../../components/Candidate/JobCard';
import styles from '../../styles/Candidate/CandidateSearchResultsStyles';
import BgResult from '../../../assets/images/Illustrasi.svg'
import myStyles from "../../styles/MyStyles";


// const NO_RESULT_IMG = { uri: 'https://cdn-icons-png.flaticon.com/512/7486/7486747.png' };
const NO_RESULT_IMG = require('../../../assets/images/Illustrasi.png');


const CandidateSearchResults = ({navigation, route}) => {
    // const { filterParams } = route.params || {};

    const [searchText, setSearchText] = useState('Design');
    const [results, setResults] = useState([]);

    useEffect(() => {


        const mockData = [
            {
                id: '1',
                title: 'Senior UI/UX Designer',
                company: 'Google inc',
                location: 'California, USA',
                salary: '$15K',
                posted: '25 minute ago',
                logo: 'https://cdn-icons-png.flaticon.com/512/2991/2991148.png',
                tags: ['Design', 'Full time', 'Senior'],
                saved: false
            },
            {
                id: '2',
                title: 'Product Designer',
                company: 'Spotify',
                location: 'New York, USA',
                salary: '$12K',
                posted: '1 hour ago',
                logo: 'https://cdn-icons-png.flaticon.com/512/174/174872.png',
                tags: ['Remote', 'Junior'],
                saved: true
            }
        ];

        setTimeout(() => {
            setResults(mockData);
        }, 500);

    },[]);
// [filterParams]

    const handleSaveJob = (jobId) => {
        setResults(prevResults =>
            prevResults.map(job =>
                job.id === jobId
                    ? {...job, saved: !job.saved}
                    : job
            )
        );
        console.log('Toggled save for:', jobId);
    };

    const renderNoResults = () => (
        <View style={styles.noResultContainer}>
            {/*<Image source={NO_RESULT_IMG} style={styles.noResultImage} />*/}
            <BgResult style={styles.noResultImage}/>
            <CustomText style={styles.noResultTitle}>No results found</CustomText>
            <CustomText style={styles.noResultText}>
                The search could not be found, please check spelling or write another word.
            </CustomText>
        </View>
    );

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <CustomHeader navigation={navigation} showMenu={false}/>

            <View style={styles.searchContainer}>
                <View style={styles.searchWrapper}>
                    <MaterialCommunityIcons name="magnify" size={24} color="#AAA6B9"/>
                    <TextInput
                        style={styles.searchInput}
                        placeholder="Search..."
                        placeholderTextColor="#AAA6B9"
                        value={searchText}
                        onChangeText={setSearchText}
                    />
                    {searchText.length > 0 && (
                        <TouchableOpacity onPress={() => setSearchText('')}>
                            <MaterialCommunityIcons name="close-circle" size={20} color="#AAA6B9"/>
                        </TouchableOpacity>
                    )}
                </View>
            </View>

            {results.length > 0 ? (
                <View style={{flex: 1}}>
                    <CustomText style={[styles.resultCount, myStyles.ml6]}>
                        Found {results.length} Jobs
                    </CustomText>
                    <FlatList
                        data={results}
                        renderItem={({item}) => (
                            <JobCard
                                item={item}
                                variant="search"
                                onApplyPress={() => console.log('Apply', item.id)}
                                // onSavePress={() => console.log('Save', item.id)}
                                onSavePress={handleSaveJob}
                            />
                        )}
                        keyExtractor={item => item.id}
                        contentContainerStyle={styles.listContent}
                        showsVerticalScrollIndicator={false}
                    />
                </View>
            ) : (
                renderNoResults()
            )}

        </SafeAreaView>
    );
};

export default CandidateSearchResults;
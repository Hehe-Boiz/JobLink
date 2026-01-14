import React, {useState, useEffect} from 'react';
import {View, TextInput, FlatList, TouchableOpacity, ActivityIndicator} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import AsyncStorage from "@react-native-async-storage/async-storage";
import CustomHeader from '../../components/common/CustomHeader';
import CustomText from '../../components/common/CustomText';
import JobCard from '../../components/Candidate/JobCard';
import BgResult from '../../../assets/images/Illustrasi.svg';
import styles from '../../styles/Candidate/CandidateSearchResultsStyles';
import myStyles from "../../styles/MyStyles";
import {authApis, endpoints} from "../../utils/Apis";
import {formatTimeElapsed} from "../../utils/Helper";

const CandidateSearchResults = ({navigation, route}) => {
    const {filterParams} = route.params || {};

    const [searchText, setSearchText] = useState('');

    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);

    const getExperienceValue = (frontendId) => {
        const map = {
            'no_experience': 'FRESHER',
            'less_than_1': 'FRESHER',
            '1_3': 'JUNIOR',
            '3_5': 'MIDDLE',
            '5_10': 'SENIOR',
            'more_than_10': 'EXPERT'
        };
        return map[frontendId] || null;
    };

    const getDateFilter = (timeId) => {
        const now = new Date();
        if (timeId === 'week') {
            now.setDate(now.getDate() - 7);
            return now.toISOString().split('T')[0];
        }
        if (timeId === 'month') {
            now.setMonth(now.getMonth() - 1);
            return now.toISOString().split('T')[0];
        }
        return null;
    };

    const fetchJobs = async () => {
        setLoading(true);
        try {
            const token = await AsyncStorage.getItem('token');
            let params = {};

            if (searchText.trim()) {
                params.search = searchText;
            }

            if (filterParams) {
                if (filterParams.category && filterParams.category.id) {
                    params.category = filterParams.category.id;
                }

                if (filterParams.location) {
                    params.location = filterParams.location.name;
                }

                if (filterParams.salary) {
                    params.min_salary = filterParams.salary.min * 1000000;
                    params.max_salary = filterParams.salary.max * 1000000;
                }

                if (filterParams.selectedJobTypes && filterParams.selectedJobTypes.length > 0) {
                    const typeMap = {
                        'full': 'FULL_TIME',
                        'part': 'PART_TIME',
                        'remote': 'REMOTE',
                        'intern': 'INTERN',
                    };
                    const firstType = filterParams.selectedJobTypes[0];
                    if (typeMap[firstType]) {
                        params.employment_type = typeMap[firstType];
                    }
                }

                if (filterParams.experience) {
                    const backendExpValue = getExperienceValue(filterParams.experience);
                    if (backendExpValue) {
                        params.experience_level = backendExpValue;
                    }
                }

                if (filterParams.lastUpdate) {
                    const dateStr = getDateFilter(filterParams.lastUpdate);
                    if (dateStr) {
                        params.created_after = dateStr;
                    }
                }

            }

            console.log("Fetching jobs with params:", params);

            let res = await authApis(token).get(endpoints['jobs'], {params});
            const apiJobs = res.data.results;

            const formattedJobs = apiJobs.map(job => {
                const minSalary = job.salary_min ? (job.salary_min / 1000000).toFixed(0) + 'M' : '';
                const maxSalary = job.salary_max ? (job.salary_max / 1000000).toFixed(0) + 'M' : '';
                const salaryString = (minSalary && maxSalary)
                    ? `${minSalary} - ${maxSalary}`
                    : (minSalary || maxSalary || 'Thỏa thuận');

                return {
                    id: job.id,
                    title: job.title,
                    company: job.company_name,
                    location: job.location?.name || 'Việt Nam',
                    salary: salaryString,
                    posted: formatTimeElapsed(job.created_date),
                    logo: job.employer_logo || 'https://via.placeholder.com/60',
                    tags: [
                        job.category?.name, // Thêm tên category vào tag
                        job.employment_type?.replace('_', ' '),
                        ...(job.tags || []).map(t => t.name || t)
                    ].filter(Boolean),
                    saved: !!job.bookmark_id,
                    bookmark_id: job.bookmark_id
                };
            });

            setResults(formattedJobs);

        } catch (error) {
            console.error("Lỗi tìm kiếm:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
    }, [filterParams]);

    const handleSearchSubmit = () => {
        fetchJobs();
    };

    const handleClearSearch = () => {
        setSearchText('');
        setTimeout(() => fetchJobs(), 0);
    };

    // Logic Bookmark (Giữ nguyên)
    const handleSaveJob = async (job) => {
        setResults(prevResults =>
            prevResults.map(j =>
                j.id === job.id ? {...j, saved: !j.saved} : j
            )
        );
        try {
            const token = await AsyncStorage.getItem('token');
            if (job.saved) {
                if (job.bookmark_id) {
                    await authApis(token).delete(`${endpoints['bookmarks']}${job.bookmark_id}/`);
                }
            } else {
                let res = await authApis(token).post(endpoints['bookmarks'], {job_id: job.id});
                setResults(prev => prev.map(j => j.id === job.id ? {...j, bookmark_id: res.data.id} : j));
            }
        } catch (error) {
            console.error("Lỗi bookmark:", error);
        }
    };

    const renderNoResults = () => (
        <View style={styles.noResultContainer}>
            <BgResult style={styles.noResultImage}/>
            <CustomText style={styles.noResultTitle}>No results found</CustomText>
            <CustomText style={styles.noResultText}>
                The search could not be found, please check spelling or write another word.
            </CustomText>
        </View>
    );

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <CustomHeader navigation={navigation} showMenu={false} title="Search Results"/>

            <View style={styles.searchContainer}>
                <View style={styles.searchWrapper}>
                    <MaterialCommunityIcons name="magnify" size={24} color="#AAA6B9"/>
                    <TextInput
                        style={styles.searchInput}
                        placeholder="Search job title, company..."
                        placeholderTextColor="#AAA6B9"
                        value={searchText}
                        onChangeText={setSearchText}
                        onSubmitEditing={handleSearchSubmit}
                        returnKeyType="search"
                    />
                    {searchText.length > 0 && (
                        <TouchableOpacity onPress={() => {
                            setSearchText('');
                        }}>
                            <MaterialCommunityIcons name="close-circle" size={20} color="#AAA6B9"/>
                        </TouchableOpacity>
                    )}
                </View>
            </View>

            {loading ? (
                <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
                    <ActivityIndicator size="large" color="#FF9228"/>
                </View>
            ) : results.length > 0 ? (
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
                                onApplyPress={() => navigation.navigate('ApplyJob', {jobId: item.id})}
                                onSavePress={() => handleSaveJob(item)}
                                onPress={() => navigation.navigate('JobDetail', {jobId: item.id})}
                            />
                        )}
                        keyExtractor={item => item.id.toString()}
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
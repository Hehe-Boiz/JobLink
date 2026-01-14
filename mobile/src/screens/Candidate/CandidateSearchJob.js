import React, {useState, useEffect, useCallback} from "react";
import {SafeAreaView} from "react-native-safe-area-context";
import {View, StyleSheet, TextInput, TouchableOpacity, ScrollView, FlatList, ActivityIndicator} from "react-native";
import BgHeader from '../../../assets/images/Background_1.svg'
import CustomHeader from "../../components/common/CustomHeader";
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from "../../components/common/CustomText";
import JobCard from "../../components/Candidate/JobCard";
import MyStyles from "../../styles/MyStyles";
import styles from '../../styles/Candidate/CandidateSearchJobStyles'
import AsyncStorage from "@react-native-async-storage/async-storage";
import {authApis, endpoints} from "../../utils/Apis";
import {useNavigation} from "@react-navigation/native";
import {formatTimeElapsed} from "../../utils/Helper";
import {useFocusEffect} from "@react-navigation/native";


const CandidateSearchJob = ({navigation}) => {
    const [search, setSearch] = useState('');
    const [locationInput, setLocationInput] = useState('');
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [categories, setCategories] = useState([]);
    const [selectedCategoryId, setSelectedCategoryId] = useState(null);

    const fetchCategories = async () => {
        try {
            const token = await AsyncStorage.getItem('token');
            let res = await authApis(token).get(endpoints['categories']);
            setCategories(res.data);
        } catch (error) {
            console.error("Lỗi tải categories:", error);
        }
    };

    const fetchJobs = async (searchTerm = '', locationTerm = '', categoryId = null) => {
        setLoading(true);
        try {
            const token = await AsyncStorage.getItem('token');
            let url = endpoints['jobs'];
            const params = {};

            if (searchTerm) params.search = searchTerm;
            if (locationTerm) params.location = locationTerm;

            if (categoryId) {
                params.category = categoryId;
            }

            const res = await authApis(token).get(url, {params});
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
                    logo: job.employer_logo || 'https://via.placeholder.com/60',
                    location: job.location?.name || 'Việt Nam',
                    salary: salaryString,
                    period: 'VND',
                    tags: [
                        job.employment_type?.replace('_', ' '),
                        ...(job.tags || []).map(t => t.name || t)
                    ].filter(Boolean),
                    bookmark_id: job.bookmark_id,
                    saved: !!job.bookmark_id,
                    posted: formatTimeElapsed(job.created_date)
                };
            });

            setJobs(formattedJobs);
        } catch (error) {
            console.error("[CandidateSearchJob] Lỗi tìm kiếm việc làm:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCategories();
    }, []);

    useFocusEffect(
        useCallback(() => {
            fetchJobs(search, locationInput, selectedCategoryId);
        }, [selectedCategoryId])
    );

    const handleCategoryPress = (catId) => {
        if (selectedCategoryId === catId) {
            console.log("Un-selecting category:", catId);
            setSelectedCategoryId(null);
            fetchJobs(search, locationInput, null);
        } else {
            console.log("Selecting category:", catId);
            setSelectedCategoryId(catId);
            fetchJobs(search, locationInput, catId);
        }
    };

    const handlePressJob = (job) => {
        navigation.navigate("JobDetail", {
            jobId: job.id,
            initialData: job
        });
    };

    const handleSaveJob = async (job) => {
        setJobs(prevJobs => prevJobs.map(j => {
            if (j.id === job.id) {
                return {...j, bookmark_id: j.bookmark_id ? null : true, saved: !j.saved};
            }
            return j;
        }));

        try {
            const token = await AsyncStorage.getItem('token');
            if (job.bookmark_id) {
                await authApis(token).delete(`${endpoints['bookmarks']}${job.bookmark_id}/`);
            } else {
                let res = await authApis(token).post(endpoints['bookmarks'], {
                    job_id: job.id
                });
                const newBookmarkId = res.data.id;
                setJobs(prevJobs => prevJobs.map(j =>
                    j.id === job.id ? {...j, bookmark_id: newBookmarkId} : j
                ));
            }
        } catch (error) {
            console.error("Lỗi bookmark:", error);
            fetchJobs(search);
        }
    };

    const handleSearchSubmit = () => {
        fetchJobs(search, locationInput);
    };

    const handleChipPress = (keyword) => {
        setSearch(keyword);
        fetchJobs(keyword, locationInput);
    };

    const renderJobItem = ({item}) => (
        <JobCard
            item={item}
            variant="search"
            onPress={() => handlePressJob(item)}
            onSavePress={() => handleSaveJob(item)}
        />
    );

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
                                    onSubmitEditing={handleSearchSubmit}
                                    returnKeyType="search"
                                />
                            </View>
                            <View style={styles.inputWrapper}>
                                <MaterialCommunityIcons name="map-marker-outline" size={20} color="#FF9228"/>
                                <TextInput
                                    style={styles.textInput}
                                    value={locationInput}
                                    onChangeText={setLocationInput}
                                    placeholder="Location"
                                    placeholderTextColor="#AAA6B9"
                                    onSubmitEditing={handleSearchSubmit}
                                />
                            </View>
                        </View>
                    </View>
                </SafeAreaView>
            </View>
            <View style={[styles.filterBar, MyStyles.mb4]} onPress={handleSearchSubmit}>
                <TouchableOpacity style={styles.filterIconBtn}
                                  onPress={() => navigation.navigate('CandidateFilterCategory', {categories: categories})}
                >
                    <MaterialCommunityIcons name="tune-variant" size={20} color="white"/>
                </TouchableOpacity>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipScroll}>
                    {categories.slice(0, 5).map((cat) => {
                        const isSelected = selectedCategoryId === cat.id;
                        return (
                            <TouchableOpacity key={cat.id}
                                              style={[styles.chipBtn, isSelected && {backgroundColor: '#FF9228'}]}
                                              onPress={() => handleCategoryPress(cat.id)}
                            >
                                <CustomText
                                    style={[styles.chipText, isSelected && {color: 'white'}]}>{cat.name}</CustomText>
                            </TouchableOpacity>
                        )
                    })}
                </ScrollView>
            </View>
            {loading ? (
                <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
                    <ActivityIndicator size="large" color="#FF9228"/>
                </View>
            ) : (
                <FlatList
                    data={jobs}
                    renderItem={renderJobItem}
                    keyExtractor={item => item.id.toString()}
                    contentContainerStyle={styles.listContent}
                    showsVerticalScrollIndicator={false}
                    ListEmptyComponent={
                        <View style={{alignItems: 'center', marginTop: 50}}>
                            <CustomText>Không tìm thấy công việc.</CustomText>
                        </View>
                    }
                />
            )}
        </View>
    )
        ;
};

export default CandidateSearchJob;


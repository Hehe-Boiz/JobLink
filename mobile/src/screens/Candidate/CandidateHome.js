import React, {useState, useEffect, useRef, useContext, useCallback} from 'react';
import {View, Image, ScrollView, Pressable, Animated, ActivityIndicator} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import CustomText from '../../components/common/CustomText';
import styles from '../../styles/Candidate/CandidateHomeStyles';
import JobCard from '../../components/Candidate/JobCard'
import {FAB} from 'react-native-paper';
import AsyncStorage from "@react-native-async-storage/async-storage";
import {useNavigation} from '@react-navigation/native';

const heroImage = require('../../../assets/images/hero.png');
const headhuntingIcon = require('../../../assets/images/headhunting.png');
import Apis, {endpoints, authApis} from '../../utils/Apis';
import {MyUserContext} from '../../utils/contexts/MyContext';
import {useFocusEffect} from '@react-navigation/native';

const getInitials = (fullName) => {
    if (!fullName) return "U";
    const names = fullName.trim().split(" ");
    if (names.length === 1) {
        return names[0].charAt(0).toUpperCase();
    }
    return (names[0].charAt(0) + names[names.length - 1].charAt(0)).toUpperCase();
};

const StatCard = ({icon, iconImage, count, label, color}) => (
    <View style={[styles.statCard, {backgroundColor: color}]}>
        {iconImage ? (
            <View style={styles.iconContainer}>
                <Image
                    source={iconImage}
                    style={styles.iconImage}
                    resizeMode="contain"
                />
            </View>
        ) : null}
        <CustomText style={styles.statCount}>{count}</CustomText>
        <CustomText style={styles.statLabel}>{label}</CustomText>
    </View>
);

const CandidateHome = () => {
    const navigation = useNavigation();
    const [jobs, setJobs] = useState([])
    const scaleSearch = useRef(new Animated.Value(1)).current;
    const [loading, setLoading] = useState(true);
    const [user] = useContext(MyUserContext);
    const [jobStats, setJobStats] = useState({
        remote: 0,
        fullTime: 0,
        partTime: 0
    });

    const loadData = async () => {
        try {
            const token = await AsyncStorage.getItem('token');
            let res = await authApis(token).get(endpoints['jobs']);
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
                        job.category?.name,
                        job.employment_type?.replace('_', ' '),
                        ...(job.tags || []).map(t => t.name || t)
                    ].filter(Boolean),
                    bookmark_id: job.bookmark_id,
                    saved: !!job.bookmark_id
                };
            });
            setJobs(formattedJobs)
            let resStats = await authApis(token).get(`${endpoints['jobs']}stats/`);

            setJobStats({
                remote: resStats.data.remote_count,
                fullTime: resStats.data.full_time_count,
                partTime: resStats.data.part_time_count
            });

        } catch (error) {
            console.error("Lỗi tải dữ liệu:", error);
        } finally {
            setLoading(false);
        }
    };

    useFocusEffect(
        useCallback(() => {
            loadData();
        }, [])
    );

    const onPressIn = () => {
        Animated.spring(scaleSearch, {
            toValue: 0.95,
            useNativeDriver: true,
        }).start();
    };

    const onPressOut = () => {
        Animated.spring(scaleSearch, {
            toValue: 1,
            useNativeDriver: true,
        }).start();
    };

    const handlePressJob = (job) => {
        navigation.navigate("JobDetail", {
            jobId: job.id,
            initialData: job
        });
    };

    const handleSaveJob = async (job) => {
        try {
            const token = await AsyncStorage.getItem('token');
            console.log(token)
            const oldJobs = [...jobs];

            setJobs(prevJobs => prevJobs.map(j => {
                if (j.id === job.id) {
                    return {...j, bookmark_id: j.bookmark_id ? null : true};
                }
                return j;
            }));

            if (job.bookmark_id) {
                await authApis(token).delete(`${endpoints['bookmarks']}${job.bookmark_id}/`);
                console.log("Đã hủy lưu job");
            } else {
                console.log(token);
                let res = await authApis(token).post(endpoints['bookmarks'], {
                    job_id: job.id
                });
                const newBookmarkId = res.data.id;
                setJobs(prevJobs => prevJobs.map(j =>
                    j.id === job.id ? {...j, bookmark_id: newBookmarkId} : j
                ));
                console.log("Đã lưu job, ID:", newBookmarkId);
            }
        } catch (error) {
            console.error("Lỗi thao tác bookmark:", error);
            alert("Có lỗi xảy ra, vui lòng thử lại.");
            loadData();
        }
    };

    const handleApplyJob = (jobId) => {
        console.log('Apply job:', jobId);
        navigation.navigate('ApplyJob', {jobId: jobId});
    };
    const displayName = user ? (user.full_name || user.username) : "Guest";

    if (loading) {
        return (
            <SafeAreaView style={[styles.container, {justifyContent: 'center', alignItems: 'center'}]}>
                <ActivityIndicator size="large" color="#FF9228"/>
                <CustomText style={{marginTop: 10, color: '#AAA6B9'}}>Đang tải việc làm...</CustomText>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            <ScrollView showsVerticalScrollIndicator={false}>
                <View style={styles.header}>
                    <View>
                        <CustomText style={styles.greeting}>Hello</CustomText>
                        <CustomText style={styles.userName}>{user.full_name}.</CustomText>
                    </View>
                    {user && user.avatar ? (
                        <Image
                            source={{uri: user.avatar}}
                            style={styles.avatar}
                        />
                    ) : (
                        <View style={[
                            styles.avatar,
                            {
                                backgroundColor: '#FF9228',
                                justifyContent: 'center',
                                alignItems: 'center'
                            }
                        ]}>
                            <CustomText style={{
                                color: '#0D0140',
                                fontSize: 20,
                                fontWeight: '900'
                            }}>
                                {getInitials(displayName)}
                            </CustomText>
                        </View>
                    )}
                </View>

                <View style={styles.banner}>
                    <View style={styles.bannerContent}>
                        <CustomText style={styles.bannerTitle}>50% off</CustomText>
                        <CustomText style={styles.bannerSubtitle}>take any courses</CustomText>
                        <Pressable
                            onPress={() => console.log('Join Now')}
                            style={({pressed}) => [
                                styles.joinButton,
                                {
                                    backgroundColor: pressed ? '#E67E22' : '#FF9228',
                                    transform: [{scale: pressed ? 0.98 : 1}]
                                }
                            ]}
                        >
                            <CustomText style={styles.joinButtonText}>Join Now</CustomText>
                        </Pressable>
                    </View>
                    <Image
                        source={heroImage}
                        style={styles.bannerImage}
                        resizeMode="contain"
                    />
                </View>

                <View style={styles.section}>
                    <CustomText style={styles.sectionTitle}>Find Your Job</CustomText>

                    <View style={styles.statsGrid}>
                        <View style={styles.statCardLarge}>
                            <StatCard
                                iconImage={headhuntingIcon}
                                count={jobStats.remote}
                                label="Remote Job"
                                color="#A0D8F1"
                            />
                        </View>

                        <View style={styles.statCardColumn}>
                            <View style={styles.statCardSmall}>
                                <View style={[styles.statCard, {backgroundColor: '#B8B5FF'}]}>
                                    <CustomText style={styles.statCount}>{jobStats.fullTime}</CustomText>
                                    <CustomText style={styles.statLabel}>Full Time</CustomText>
                                </View>
                            </View>

                            <View style={styles.statCardSmall}>
                                <View style={[styles.statCard, {backgroundColor: '#FFD6AD'}]}>
                                    <CustomText style={styles.statCount}>{jobStats.partTime}</CustomText>
                                    <CustomText style={styles.statLabel}>Part Time</CustomText>
                                </View>
                            </View>
                        </View>
                    </View>
                </View>

                <View style={styles.section}>
                    <CustomText style={styles.sectionTitle}>Recent Job List</CustomText>

                    {jobs.map((job) => (
                        <JobCard
                            key={job.id}
                            item={{
                                ...job,
                                saved: !!job.bookmark_id
                            }}
                            onSavePress={() => handleSaveJob(job)}
                            onApplyPress={() => handleApplyJob(job.id)}
                            onPress={() => handlePressJob(job)}
                        />
                    ))}
                </View>
            </ScrollView>
            <Animated.View style={{transform: [{scale: scaleSearch}]}}>
                <FAB
                    icon="magnify"
                    style={styles.fabSearch}
                    color="#130160"
                    onPress={() => navigation.navigate('CandidateSearchJob')}
                    rippleColor="rgba(19, 1, 96, 0.1)"
                    onPressIn={onPressIn}
                    onPressOut={onPressOut}
                />
            </Animated.View>
        </SafeAreaView>
    );
};

export default CandidateHome;
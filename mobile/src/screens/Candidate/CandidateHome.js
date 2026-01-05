import React, {useState} from 'react';
import {View, Image, ScrollView, Pressable, Animated} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import CustomText from '../../components/CustomText';
import styles from '../../styles/Candidate/CandidateHomeStyles';
import JobCard from '../../components/Candidate/JobCard'
import {FAB} from 'react-native-paper';
import {useRef} from "react";
const heroImage = require('../../../assets/images/hero.png');
const headhuntingIcon = require('../../../assets/images/headhunting.png');

const MOCK_JOBS = [
    {
        id: '1',
        title: 'Product Designer',
        company: 'Google inc',
        location: 'California, USA',
        salary: '$15K',
        period: 'Mo',
        logo: 'https://www.google.com/url?sa=t&source=web&rct=j&url=https%3A%2F%2Fvi.wikipedia.org%2Fwiki%2FT%25E1%25BA%25ADp_tin%3AApple_logo_black.svg&ved=0CBUQjRxqFwoTCKiqmeCG8pEDFQAAAAAdAAAAABAH&opi=89978449',
        tags: ['Senior designer', 'Full time'],
        saved: false,
    },
    {
        id: '2',
        title: 'Senior React Native Developer',
        company: 'Tech Solutions Co.',
        location: 'Quận 1, TP. HCM',
        salary: '25M - 40M',
        period: 'VND',
        logo: 'https://via.placeholder.com/60',
        tags: ['Full-time', 'Remote'],
        saved: true,
    },
    {
        id: '3',
        title: 'UI/UX Designer',
        company: 'Creative Studio',
        location: 'Cầu Giấy, Hà Nội',
        salary: '15M - 25M',
        period: 'VND',
        logo: 'https://via.placeholder.com/60',
        tags: ['Remote', 'Part-time'],
        saved: false,
    },
];

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
    const [jobs, setJobs] = useState(MOCK_JOBS)
    const scaleSearch = useRef(new Animated.Value(1)).current;

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
    const handleSaveJob = (jobId) => {
        setJobs(prevJobs =>
            prevJobs.map(job =>
                job.id === jobId
                    ? {...job, saved: !job.saved}
                    : job
            )
        );
        console.log('Toggled save for job:', jobId);
    };

    const handleApplyJob = (jobId) => {
        console.log('Apply job:', jobId);
    };

    return (
        <SafeAreaView style={styles.container} edges={['top']}>
            <ScrollView showsVerticalScrollIndicator={false}>
                <View style={styles.header}>
                    <View>
                        <CustomText style={styles.greeting}>Hello</CustomText>
                        <CustomText style={styles.userName}>Orlando Diggs.</CustomText>
                    </View>
                    <Image
                        source={{uri: 'https://i.pravatar.cc/100'}}
                        style={styles.avatar}
                    />
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
                                count="44.5k"
                                label="Remote Job"
                                color="#A0D8F1"
                            />
                        </View>

                        <View style={styles.statCardColumn}>
                            <View style={styles.statCardSmall}>
                                <View style={[styles.statCard, {backgroundColor: '#B8B5FF'}]}>
                                    <CustomText style={styles.statCount}>66.8k</CustomText>
                                    <CustomText style={styles.statLabel}>Full Time</CustomText>
                                </View>
                            </View>

                            <View style={styles.statCardSmall}>
                                <View style={[styles.statCard, {backgroundColor: '#FFD6AD'}]}>
                                    <CustomText style={styles.statCount}>38.9k</CustomText>
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
                            item={job}
                            onSavePress={handleSaveJob}
                            onApplyPress={handleApplyJob}
                        />
                    ))}
                </View>
            </ScrollView>
            <Animated.View style={{transform: [{scale: scaleSearch}]}}>
                <FAB
                    icon="magnify"
                    style={styles.fabSearch}
                    color="#130160"
                    onPress={() => console.log('Search Pressed')}
                    rippleColor="rgba(19, 1, 96, 0.1)"
                    onPressIn={onPressIn}
                    onPressOut={onPressOut}
                />
            </Animated.View>
        </SafeAreaView>
    );
};

export default CandidateHome;
import React, {useState} from 'react';
import {View, TouchableOpacity, Image, ScrollView, Animated, Pressable} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/CustomText';
import styles from '../../styles/Candidate/CandidateHomeStyles';
import {TouchableRipple} from 'react-native-paper';

const heroImage = require('../../../assets/hero.png');
const headhuntingIcon = require('../../../assets/headhunting.png');

// Mock Data
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

const JobCard = ({item, onSavePress, onApplyPress}) => {
    const scaleValue = new Animated.Value(1);
    const bookmarkScale = new Animated.Value(1);

    const animateBookmark = (toValue) => {
        Animated.spring(bookmarkScale, {
            toValue,
            useNativeDriver: true,
            friction: 4,
            tension: 40,
        }).start();
    };

    const onPressIn = () => {
        Animated.spring(scaleValue, {
            toValue: 0.97,
            useNativeDriver: true,
        }).start();
    };

    const onPressOut = () => {
        Animated.spring(scaleValue, {
            toValue: 1,
            useNativeDriver: true,
        }).start();
    };

    return (
        <Animated.View style={{transform: [{scale: scaleValue}]}}>
            <TouchableRipple
                onPress={() => console.log('Job Pressed')}
                onPressIn={onPressIn}
                onPressOut={onPressOut}
                rippleColor="rgba(19, 1, 96, 0.1)"
                style={styles.jobCard}
            >
                <View>
                    <View style={styles.jobCardHeader}>
                        <View style={styles.jobCardLeft}>
                            <View style={styles.logoContainer}>
                                <Image
                                    source={{uri: item.logo}}
                                    style={styles.companyLogo}
                                    resizeMode="contain"
                                />
                            </View>
                            <View style={styles.jobInfo}>
                                <CustomText style={styles.jobTitle}>{item.title}</CustomText>
                                <CustomText style={styles.companyInfo}>
                                    {item.company} • {item.location}
                                </CustomText>
                            </View>
                        </View>
                        <Animated.View style={{transform: [{scale: bookmarkScale}]}}>
                            <TouchableRipple
                                borderless
                                centered
                                onPress={() => onSavePress(item.id)}
                                onPressIn={() => animateBookmark(1.2)}
                                onPressOut={() => animateBookmark(1)}
                                rippleColor="rgba(16, 91, 230, 0.2)"
                                style={{padding: 8, borderRadius: 20}}
                            >
                                <MaterialCommunityIcons
                                    name={item.saved ? "bookmark" : "bookmark-outline"}
                                    size={24}
                                    color={item.saved ? "#105be6ff" : "#95969D"}
                                />
                            </TouchableRipple>
                        </Animated.View>
                    </View>

                    <View style={styles.salaryContainer}>
                        <CustomText style={styles.salary}>
                            {item.salary}
                            <CustomText style={styles.salaryPeriod}>/{item.period}</CustomText>
                        </CustomText>
                    </View>

                    <View style={styles.jobFooter}>
                        <View style={styles.tagsContainer}>
                            {item.tags.map((tag, index) => (
                                <View key={index} style={styles.tag}>
                                    <CustomText style={styles.tagText}>{tag}</CustomText>
                                </View>
                            ))}
                        </View>

                        <Pressable
                            style={({pressed}) => [
                                styles.applyButton,
                                {opacity: pressed ? 0.7 : 1}
                            ]}
                            onPress={() => onApplyPress(item.id)}
                        >
                            <CustomText style={styles.applyButtonText}>Apply</CustomText>
                        </Pressable>
                    </View>
                </View>
            </TouchableRipple>
        </Animated.View>
    );
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
    const [jobs, setJobs] = useState(MOCK_JOBS)

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
        </SafeAreaView>
    );
};

export default CandidateHome;
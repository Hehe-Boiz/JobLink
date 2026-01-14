import React, {useContext, useState, useEffect} from 'react';
import {View, ScrollView, Image, TouchableOpacity, ActivityIndicator} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import CustomText from '../../components/common/CustomText';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import BgHeader from '../../../assets/images/Background_1.svg';
import styles from '../../styles/CandidateProfile/CandidateProfileStyles';
import {MyUserContext} from "../../utils/contexts/MyContext";
import {authApis, endpoints} from "../../utils/Apis";
import {useIsFocused} from '@react-navigation/native';
import AsyncStorage from "@react-native-async-storage/async-storage";


const SectionHeader = ({icon, title, onAdd, onEdit, hasData}) => (
    <View style={styles.sectionHeader}>
        <View style={styles.sectionHeaderLeft}>
            <View style={styles.sectionIconContainer}>
                <MaterialCommunityIcons name={icon} size={22} color="#FF9228"/>
            </View>
            <CustomText style={styles.sectionTitle}>{title}</CustomText>
        </View>
        <TouchableOpacity onPress={hasData ? onEdit : onAdd} style={styles.sectionHeaderBtn}>
            <MaterialCommunityIcons
                name={hasData ? "pencil-outline" : "plus"}
                size={20}
                color="#FF9228"
            />
        </TouchableOpacity>
    </View>
);

const AboutMeSection = ({data, onAdd, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader icon="account-outline" title="About me" hasData={!!data} onEdit={onEdit} onAdd={onAdd}/>
        {data ? <CustomText style={styles.aboutText}>{data}</CustomText> :
            <CustomText style={{color: '#999', fontStyle: 'italic'}}>Add a bio...</CustomText>}
    </View>
);

const WorkExperienceSection = ({data, onAdd, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader icon="briefcase-outline" title="Work experience" hasData={false} onAdd={onAdd}/>
        {data?.map((item) => (
            <View key={item.id} style={styles.experienceItem}>
                <View style={styles.experienceContent}>
                    <CustomText style={styles.experienceTitle}>{item.title}</CustomText>
                    <CustomText style={styles.experienceCompany}>{item.company}</CustomText>
                    <CustomText
                        style={styles.experienceDate}>{item.startDate} - {item.endDate} • {item.duration}</CustomText>
                </View>
                <TouchableOpacity onPress={() => onEdit(item)}>
                    <MaterialCommunityIcons name="pencil-outline" size={20} color="#FF9228"/>
                </TouchableOpacity>
            </View>
        ))}
    </View>
);

const EducationSection = ({data, onAdd, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader icon="school-outline" title="Education" hasData={false} onAdd={onAdd}/>
        {data?.map((item) => (
            <View key={item.id} style={styles.experienceItem}>
                <View style={styles.experienceContent}>
                    <CustomText style={styles.experienceTitle}>{item.degree}</CustomText>
                    <CustomText style={styles.experienceCompany}>{item.school}</CustomText>
                    <CustomText style={styles.experienceDate}>{item.startDate} - {item.endDate}</CustomText>
                </View>
                <TouchableOpacity onPress={() => onEdit(item)}>
                    <MaterialCommunityIcons name="pencil-outline" size={20} color="#FF9228"/>
                </TouchableOpacity>
            </View>
        ))}
    </View>
);

const SkillsSection = ({data, onEdit}) => {
    const visibleSkills = data?.slice(0, 5) || [];
    const moreCount = (data?.length || 0) - 5;
    return (
        <View style={styles.card}>
            <SectionHeader icon="star-four-points-outline" title="Skill" hasData={data?.length > 0} onEdit={onEdit}/>
            <View style={styles.tagsContainer}>
                {visibleSkills.map((skill, index) => (
                    <View key={index} style={styles.tag}><CustomText style={styles.tagText}>{skill}</CustomText></View>
                ))}
                {moreCount > 0 && (
                    <View style={[styles.tag, styles.tagMore]}><CustomText
                        style={styles.tagTextMore}>+{moreCount} more</CustomText></View>
                )}
            </View>
        </View>
    );
};

const LanguageSection = ({data, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader icon="translate" title="Language" hasData={data?.length > 0} onEdit={onEdit}/>
        <View style={styles.tagsContainer}>
            {data?.map((lang, index) => (
                <View key={index} style={styles.tag}><CustomText style={styles.tagText}>{lang}</CustomText></View>
            ))}
        </View>
    </View>
);

const AppreciationSection = ({data, onAdd, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader icon="medal-outline" title="Appreciation" hasData={false} onAdd={onAdd}/>
        {data?.map((item) => (
            <View key={item.id} style={styles.experienceItem}>
                <View style={styles.experienceContent}>
                    <CustomText style={styles.experienceTitle}>{item.title}</CustomText>
                    <CustomText style={styles.experienceCompany}>{item.subtitle}</CustomText>
                    <CustomText style={styles.experienceDate}>{item.year}</CustomText>
                </View>
                <TouchableOpacity onPress={() => onEdit(item)}>
                    <MaterialCommunityIcons name="pencil-outline" size={20} color="#FF9228"/>
                </TouchableOpacity>
            </View>
        ))}
    </View>
);

const ResumeSection = ({data, onAdd, onDelete}) => (
    <View style={styles.card}>
        <SectionHeader icon="file-document-outline" title="Resume" hasData={false} onAdd={onAdd}/>
        {data && (
            <View style={styles.resumeItem}>
                <View style={styles.resumeIconContainer}>
                    <MaterialCommunityIcons name="file-pdf-box" size={32} color="#E53935"/>
                </View>
                <View style={styles.resumeContent}>
                    <CustomText style={styles.resumeName} numberOfLines={1}>{data.name}</CustomText>
                    <CustomText style={styles.resumeInfo}>{data.size} • {data.date}</CustomText>
                </View>
                <TouchableOpacity onPress={onDelete} style={styles.deleteBtn}>
                    <MaterialCommunityIcons name="trash-can-outline" size={22} color="#FF6B6B"/>
                </TouchableOpacity>
            </View>
        )}
    </View>
);

const MOCK_DATA = {
    workExperience: [
        {
            id: '1',
            title: 'Manager',
            company: 'Amazon Inc',
            startDate: 'Jan 2015',
            endDate: 'Feb 2022',
            duration: '5 Years'
        }
    ],
    education: [
        {
            id: '1',
            degree: 'Information Technology',
            school: 'University of Oxford',
            startDate: 'Sep 2010',
            endDate: 'Aug 2013'
        }
    ],
    skills: ['Leadership', 'Teamwork', 'Visioner', 'Target oriented'],
    languages: ['English', 'German', 'Spanish'],
    appreciation: [
        {id: '1', title: 'Wireless Symposium (RWS)', subtitle: 'Young Scientist', year: '2014'}
    ],
    resume: {name: 'Jamet kudasi - CV - UI/UX Designer', size: '867 Kb', date: '14 Feb 2022'}
};

const CandidateProfile = ({navigation}) => {
    const [user, dispatch] = useContext(MyUserContext);
    const [profileData, setProfileData] = useState(null);
    const [loading, setLoading] = useState(true);
    const isFocused = useIsFocused(); // Hook để biết khi nào màn hình này được focus lại

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const token = await AsyncStorage.getItem('token');
                if (!token) {
                    setLoading(false);
                    return;
                }

                const res = await authApis(token).get(endpoints.candidate_profile);
                const backendData = res.data;

                setProfileData({
                    fullName: backendData.user.full_name,
                    avatar: backendData.user.avatar,
                    location: backendData.address || "No Address",
                    aboutMe: backendData.user.bio,
                    follower: 120,
                    following: 23,
                    ...MOCK_DATA
                });

            } catch (err) {
                console.error("Lỗi fetch profile:", err);
            } finally {
                setLoading(false);
            }
        };

        if (isFocused) {
            fetchProfile();
        }
    }, [isFocused, user]);

    if (loading) {
        return (
            <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
                <ActivityIndicator size="large" color="#FF9228"/>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.headerContainer}>
                <BgHeader width="100%" height="400" style={styles.bg} preserveAspectRatio="none"/>
                <SafeAreaView edges={['top']}>
                    <View style={styles.profileContent}>
                        <View style={styles.topBar}>
                            <Image
                                source={profileData?.avatar ? {uri: profileData.avatar.startsWith('http') ? profileData.avatar : `http://192.168.1.23:8000${profileData.avatar}`} : {uri: 'https://i.pravatar.cc/300'}}
                                style={styles.avatar}
                            />
                            <View style={styles.topIcons}>
                                <TouchableOpacity style={styles.iconButton}>
                                    <MaterialCommunityIcons name="share-variant-outline" size={24} color="#FFF"/>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    style={styles.iconButton}
                                    onPress={() => navigation.navigate('SettingsScreen')} // Chuyển sang Settings
                                >
                                    <MaterialCommunityIcons name="cog-outline" size={24} color="#FFF"/>
                                </TouchableOpacity>
                            </View>
                        </View>

                        <CustomText style={styles.name}>{profileData?.fullName || "User Name"}</CustomText>
                        <CustomText style={styles.location}>{profileData?.location}</CustomText>

                        <View style={styles.statsRow}>
                            <View style={styles.statsGroup}>
                                <CustomText style={styles.statNumber}>{profileData?.follower}k</CustomText>
                                <CustomText style={styles.statLabel}> Follower</CustomText>
                            </View>
                            <View style={styles.statsGroup}>
                                <CustomText style={styles.statNumber}>{profileData?.following}k</CustomText>
                                <CustomText style={styles.statLabel}> Following</CustomText>
                            </View>

                            <TouchableOpacity
                                style={styles.editButton}
                                activeOpacity={0.8}
                                onPress={() => navigation.navigate('EditProfile')}
                            >
                                <CustomText style={styles.editButtonText}>Edit profile</CustomText>
                                <MaterialCommunityIcons name="pencil-outline" size={16} color="#FFF"/>
                            </TouchableOpacity>
                        </View>
                    </View>
                </SafeAreaView>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.listContainer}>

                <AboutMeSection
                    data={profileData?.aboutMe}
                    onEdit={() => navigation.navigate('EditAboutMe', {aboutMe: profileData?.aboutMe})}
                    onAdd={() => navigation.navigate('EditAboutMe')}
                />

                <WorkExperienceSection
                    data={profileData?.workExperience}
                    onAdd={() => navigation.navigate('AddWorkExperience')}
                    onEdit={(item) => navigation.navigate('AddWorkExperience', {experience: item, isEdit: true})}
                />

                <EducationSection
                    data={profileData?.education}
                    onAdd={() => navigation.navigate('AddEducation')}
                    onEdit={(item) => navigation.navigate('AddEducation', {education: item, isEdit: true})}
                />

                <SkillsSection
                    data={profileData?.skills}
                    onEdit={() => navigation.navigate('SkillList', {skills: profileData?.skills})}
                />

                <LanguageSection
                    data={profileData?.languages}
                    onEdit={() => navigation.navigate('LanguageList', {languages: profileData?.languages})}
                />

                <AppreciationSection
                    data={profileData?.appreciation}
                    onAdd={() => navigation.navigate('AppreciationForm')}
                    onEdit={(item) => navigation.navigate('AppreciationForm', {appreciation: item, isEdit: true})}
                />

                <ResumeSection
                    data={profileData?.resume}
                    onAdd={() => navigation.navigate('AddResume')}
                    onDelete={() => console.log('Delete resume logic')}
                />

                <View style={{height: 100}}/>
            </ScrollView>
        </View>
    );
};

export default CandidateProfile;
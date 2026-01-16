import React, {useContext, useState, useEffect, useCallback} from 'react';
import {View, ScrollView, Image, TouchableOpacity, ActivityIndicator, Alert} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import CustomText from '../../components/common/CustomText';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import BgHeader from '../../../assets/images/Background_1.svg';
import styles from '../../styles/CandidateProfile/CandidateProfileStyles';
import {MyUserContext} from "../../utils/contexts/MyContext";
import {authApis, endpoints} from "../../utils/Apis";
import {useIsFocused, useFocusEffect} from '@react-navigation/native';
import AsyncStorage from "@react-native-async-storage/async-storage";
import {ALL_LANGUAGES} from './AddLanguage';
import ConfirmationSheet from "../../components/common/ConfirmationSheet";


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
                        style={styles.experienceDate}>{item.startDate} - {item.endDate}</CustomText>
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

const SkillsSection = ({data, onEdit, onAdd}) => {
    const visibleSkills = data?.slice(0, 5) || [];
    const moreCount = (data?.length || 0) - 5;
    return (
        <View style={styles.card}>
            <SectionHeader icon="star-four-points-outline" title="Skill" hasData={data?.length > 0} onEdit={onEdit}
                           onAdd={onAdd}/>
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

const LanguageSection = ({data, onEdit, onAdd}) => (
    <View style={styles.card}>
        <SectionHeader icon="translate" title="Language" hasData={data?.length > 0} onEdit={onEdit} onAdd={onAdd}/>
        <View style={styles.tagsContainer}>
            {data?.map((item) => (
                <View key={item.id} style={styles.tag}><CustomText
                    style={styles.tagText}>{item.language} {item.is_first_language ? "(Native)" : ""}</CustomText></View>
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

const CandidateProfile = ({navigation}) => {
    const [user, dispatch] = useContext(MyUserContext);
    const [profileData, setProfileData] = useState(null);
    const [loading, setLoading] = useState(true);
    const isFocused = useIsFocused();
    const [showDeleteResume, setShowDeleteResume] = useState(false);


    const fetchProfile = useCallback(async () => {
        try {
            const token = await AsyncStorage.getItem('token');
            if (!token) {
                setLoading(false);
                return;
            }

            const res = await authApis(token).get(endpoints.candidate_profile);
            const data = res.data;

            const mappedData = {
                fullName: data.user.full_name,
                avatar: data.user.avatar,
                location: data.address || "Chưa cập nhật",
                aboutMe: data.user.bio,
                follower: 0,
                following: 0,
                email: data.user.email,
                phone: data.user.phone,
                dob: data.dob,
                gender: data.gender,

                skills: data.skill_list?.map(s => s.name) || [],

                workExperience: data.work_experiences?.map(w => ({
                    id: w.id,
                    title: w.job_title || w.title,
                    company: w.company_name || w.company,
                    startDate: w.start_date,
                    endDate: w.end_date ? w.end_date : "Present",
                    description: w.description
                })) || [],

                education: data.educations?.map(e => ({
                    id: e.id,
                    degree: e.level ? `${e.level} - ${e.field_of_study}` : e.field_of_study,
                    school: e.institution,
                    startDate: e.start_date,
                    endDate: e.end_date ? e.end_date : "Present",
                    description: e.description
                })) || [],

                languages: data.languages?.map(lang => ({
                    ...lang,
                    flag: ALL_LANGUAGES[lang.language] || 'https://flagcdn.com/w160/gb.png' // Fallback flag nếu không tìm thấy
                })) || [],

                appreciation: data.appreciations?.map(a => ({
                    id: a.id,
                    title: a.award_name,
                    subtitle: a.category,
                    year: a.end_date,
                    description: a.description
                })) || [],
                resume: data.resume ? {
                    name: data.resume_name || "My Resume.pdf",
                    size: "PDF",
                    date: "Uploaded",
                    uri: data.resume
                } : null,
            };
            setProfileData(mappedData);

        } catch (err) {
            console.error("Lỗi fetch profile:", err);
        } finally {
            setLoading(false);
        }
    }, [user]);

    const handleDeleteResume = () => {
        setShowDeleteResume(true);
    };

    const onConfirmDelete = async () => {
        setShowDeleteResume(false);

        try {
            setLoading(true);
            const token = await AsyncStorage.getItem('token');

            await authApis(token).delete(`${endpoints.candidate_profile}resume/`);

            await fetchProfile();

        } catch (err) {
            console.error("Delete error:", err);
            Alert.alert("Error", "Could not delete resume.");
        } finally {
            setLoading(false);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchProfile();
        }, [])
    );

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
                                    onPress={() => navigation.navigate('SettingsScreen')}
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
                                onPress={() => navigation.navigate('EditProfile',{
                                    data: profileData,
                                    onSave: fetchProfile
                                })}
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
                    onEdit={() => navigation.navigate('AddSkill', {skills: profileData?.skills})}
                    onAdd={() => navigation.navigate('AddSkill')}
                />

                <LanguageSection
                    data={profileData?.languages}
                    onAdd={() => navigation.navigate('AddLanguage', {onSelect: fetchProfile})}
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
                    onDelete={handleDeleteResume}
                />

                <View style={{height: 100}}/>
            </ScrollView>
            <ConfirmationSheet
                visible={showDeleteResume}
                onConfirm={onConfirmDelete}
                onClose={() => setShowDeleteResume(false)}
                type="remove_resume"
            />
            {loading && (
                <View style={{
                    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.3)', justifyContent: 'center', alignItems: 'center'
                }}>
                    <ActivityIndicator size="large" color="#FF9228"/>
                </View>
            )}
        </View>
    );
};

export default CandidateProfile;
import React from 'react';
import {View, ScrollView, Image, TouchableOpacity} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import CustomText from '../../components/common/CustomText';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import BgHeader from '../../../assets/images/Background_1.svg';
import EditAboutMe from "./EditAboutMe";
import styles from '../../styles/CandidateProfile/CandidateProfileStyles'

const PROFILE_DATA = {
    aboutMe: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lectus id commodo egestas metus interdum dolor.",
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
            endDate: 'Aug 2013',
            duration: '5 Years'
        }
    ],
    skills: ['Leadership', 'Teamwork', 'Visioner', 'Target oriented', 'Consistent'],
    languages: ['English', 'German', 'Spanish', 'Mandarin', 'Italy'],
    appreciation: [
        {
            id: '1',
            title: 'Wireless Symposium (RWS)',
            subtitle: 'Young Scientist',
            year: '2014'
        }
    ],
    resume: {
        name: 'Jamet kudasi - CV - UI/UX Designer',
        size: '867 Kb',
        date: '14 Feb 2022 at 11:30 am'
    }
};

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

const AboutMeSection = ({data, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader
            icon="account-outline"
            title="About me"
            hasData={!!data}
            onEdit={onEdit}
        />
        {data && (
            <CustomText style={styles.aboutText}>{data}</CustomText>
        )}
    </View>
);

const WorkExperienceSection = ({data, onAdd, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader
            icon="briefcase-outline"
            title="Work experience"
            hasData={false}
            onAdd={onAdd}
        />
        {data?.map((item) => (
            <View key={item.id} style={styles.experienceItem}>
                <View style={styles.experienceContent}>
                    <CustomText style={styles.experienceTitle}>{item.title}</CustomText>
                    <CustomText style={styles.experienceCompany}>{item.company}</CustomText>
                    <CustomText style={styles.experienceDate}>
                        {item.startDate} - {item.endDate} • {item.duration}
                    </CustomText>
                </View>
                <TouchableOpacity onPress={() => onEdit(item.id)}>
                    <MaterialCommunityIcons name="pencil-outline" size={20} color="#FF9228"/>
                </TouchableOpacity>
            </View>
        ))}
    </View>
);

const EducationSection = ({data, onAdd, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader
            icon="school-outline"
            title="Education"
            hasData={false}
            onAdd={onAdd}
        />
        {data?.map((item) => (
            <View key={item.id} style={styles.experienceItem}>
                <View style={styles.experienceContent}>
                    <CustomText style={styles.experienceTitle}>{item.degree}</CustomText>
                    <CustomText style={styles.experienceCompany}>{item.school}</CustomText>
                    <CustomText style={styles.experienceDate}>
                        {item.startDate} - {item.endDate} • {item.duration}
                    </CustomText>
                </View>
                <TouchableOpacity onPress={() => onEdit(item.id)}>
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
            <SectionHeader
                icon="star-four-points-outline"
                title="Skill"
                hasData={data?.length > 0}
                onEdit={onEdit}
            />
            {data?.length > 0 && (
                <>
                    <View style={styles.tagsContainer}>
                        {visibleSkills.map((skill, index) => (
                            <View key={index} style={styles.tag}>
                                <CustomText style={styles.tagText}>{skill}</CustomText>
                            </View>
                        ))}
                        {moreCount > 0 && (
                            <View style={[styles.tag, styles.tagMore]}>
                                <CustomText style={styles.tagTextMore}>+{moreCount} more</CustomText>
                            </View>
                        )}
                    </View>
                    <TouchableOpacity style={styles.seeMoreBtn}>
                        <CustomText style={styles.seeMoreText}>See more</CustomText>
                    </TouchableOpacity>
                </>
            )}
        </View>
    );
};

const LanguageSection = ({data, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader
            icon="translate"
            title="Language"
            hasData={data?.length > 0}
            onEdit={onEdit}
        />
        {data?.length > 0 && (
            <View style={styles.tagsContainer}>
                {data.map((lang, index) => (
                    <View key={index} style={styles.tag}>
                        <CustomText style={styles.tagText}>{lang}</CustomText>
                    </View>
                ))}
            </View>
        )}
    </View>
);

const AppreciationSection = ({data, onAdd, onEdit}) => (
    <View style={styles.card}>
        <SectionHeader
            icon="medal-outline"
            title="Appreciation"
            hasData={false}
            onAdd={onAdd}
        />
        {data?.map((item) => (
            <View key={item.id} style={styles.experienceItem}>
                <View style={styles.experienceContent}>
                    <CustomText style={styles.experienceTitle}>{item.title}</CustomText>
                    <CustomText style={styles.experienceCompany}>{item.subtitle}</CustomText>
                    <CustomText style={styles.experienceDate}>{item.year}</CustomText>
                </View>
                <TouchableOpacity onPress={() => onEdit(item.id)}>
                    <MaterialCommunityIcons name="pencil-outline" size={20} color="#FF9228"/>
                </TouchableOpacity>
            </View>
        ))}
    </View>
);

const ResumeSection = ({data, onAdd, onDelete}) => (
    <View style={styles.card}>
        <SectionHeader
            icon="file-document-outline"
            title="Resume"
            hasData={false}
            onAdd={onAdd}
        />
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

    return (
        <View style={styles.container}>
            <View style={styles.headerContainer}>
                <BgHeader
                    width="100%"
                    height="400"
                    style={styles.bg}
                    preserveAspectRatio="none"
                />

                <SafeAreaView edges={['top']}>
                    <View style={styles.profileContent}>
                        <View style={styles.topBar}>
                            <Image
                                source={{uri: 'https://i.pravatar.cc/300?img=12'}}
                                style={styles.avatar}
                            />
                            <View style={styles.topIcons}>
                                <TouchableOpacity style={styles.iconButton}>
                                    <MaterialCommunityIcons name="share-variant-outline" size={24} color="#FFF"/>
                                </TouchableOpacity>
                                <TouchableOpacity style={styles.iconButton}>
                                    <MaterialCommunityIcons name="cog-outline" size={24} color="#FFF"/>
                                </TouchableOpacity>
                            </View>
                        </View>
                        <CustomText style={styles.name}>Orlando Diggs</CustomText>
                        <CustomText style={styles.location}>California, USA</CustomText>

                        <View style={styles.statsRow}>
                            <View style={styles.statsGroup}>
                                <CustomText style={styles.statNumber}>120k</CustomText>
                                <CustomText style={styles.statLabel}> Follower</CustomText>
                            </View>

                            <View style={styles.statsGroup}>
                                <CustomText style={styles.statNumber}>23k</CustomText>
                                <CustomText style={styles.statLabel}> Following</CustomText>
                            </View>

                            <TouchableOpacity style={styles.editButton} activeOpacity={0.8}>
                                <CustomText style={styles.editButtonText}>Edit profile</CustomText>
                                <MaterialCommunityIcons name="pencil-outline" size={16} color="#FFF"/>
                            </TouchableOpacity>
                        </View>
                    </View>
                </SafeAreaView>
            </View>

            <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.listContainer}
            >
                <AboutMeSection
                    data={PROFILE_DATA.aboutMe}
                    onEdit={() => navigation.navigate('EditAboutMe', { aboutMe: PROFILE_DATA.aboutMe })}
                />

                <WorkExperienceSection
                    data={PROFILE_DATA.workExperience}
                    onAdd={() => console.log('Add work experience')}
                    onEdit={(id) => console.log('Edit work experience', id)}
                />

                <EducationSection
                    data={PROFILE_DATA.education}
                    onAdd={() => console.log('Add education')}
                    onEdit={(id) => console.log('Edit education', id)}
                />

                <SkillsSection
                    data={PROFILE_DATA.skills}
                    onEdit={() => console.log('Edit skills')}
                />

                <LanguageSection
                    data={PROFILE_DATA.languages}
                    onEdit={() => console.log('Edit languages')}
                />

                <AppreciationSection
                    data={PROFILE_DATA.appreciation}
                    onAdd={() => console.log('Add appreciation')}
                    onEdit={(id) => console.log('Edit appreciation', id)}
                />

                <ResumeSection
                    data={PROFILE_DATA.resume}
                    onAdd={() => console.log('Add resume')}
                    onDelete={() => console.log('Delete resume')}
                />

                <View style={{height: 100}}/>
            </ScrollView>
        </View>
    );
};



export default CandidateProfile;
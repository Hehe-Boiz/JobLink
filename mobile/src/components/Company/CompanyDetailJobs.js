import React from 'react';
import { View, FlatList, StyleSheet } from 'react-native';
import JobCard from '../Candidate/JobCard';

const MOCK_COMPANY_JOBS = [
    {
        id: '1',
        title: 'UI/UX Designer',
        company: 'Google inc',
        location: 'California, USA',
        salary: '$15K',
        period: 'Mo',
        posted: '25 minute ago',
        logo: 'https://cdn-icons-png.flaticon.com/512/2991/2991148.png',
        tags: ['Design', 'Full time', 'Senior'],
        saved: false
    },
    {
        id: '2',
        title: 'IT Programmer',
        company: 'Google inc',
        location: 'California, USA',
        salary: '$20K',
        period: 'Mo',
        posted: '45 minute ago',
        logo: 'https://cdn-icons-png.flaticon.com/512/2991/2991148.png',
        tags: ['Programmer', 'Full time', 'Senior'],
        saved: false
    }
];

const CompanyDetailJobs = ({ navigation }) => {
    return (
        <View style={styles.container}>
            {MOCK_COMPANY_JOBS.map((item) => (
                <View key={item.id} style={{ marginBottom: 15 }}>
                    <JobCard
                        item={item}
                        variant="search"
                        onApplyPress={() => console.log('Apply')}
                        onSavePress={() => console.log('Save')}
                    />
                </View>
            ))}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        paddingHorizontal: 20,
        paddingBottom: 20,
    }
});

export default CompanyDetailJobs;
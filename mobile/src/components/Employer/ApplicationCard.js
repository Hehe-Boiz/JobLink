import React from 'react';
import { View, Image, Text } from 'react-native';
import { Card, Button, IconButton } from 'react-native-paper';
import styles from '../../styles/Employer/EmployerHomeStyles'; 

const ApplicantCard = ({ item, onReviewPress }) => {
  return (
    <Card style={styles.jobCard} mode="elevated">
        <Card.Content>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
                    <View style={styles.logoBox}>
                        <Image source={{ uri: item.avatar }} style={{ width: 40, height: 40, borderRadius: 8 }} />
                    </View>
                    <View style={{ marginLeft: 12 }}>
                        <Text style={{ fontWeight: 'bold', fontSize: 16 }}>{item.position}</Text>
                        <Text style={{ color: '#95969D', fontSize: 12 }}>{item.name}</Text>
                    </View>
                </View>
                <IconButton icon="bookmark-outline" size={24} iconColor="#95969D" style={{ margin: 0 }} />
            </View>

            <View style={{ marginVertical: 12 }}>
                <Text style={{ fontWeight: 'bold', fontSize: 14 }}>
                    {item.salary_expect} <Text style={{ color: '#95969D', fontWeight: 'normal' }}>/Mo (Expect)</Text>
                </Text>
            </View>

            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <View style={{ flexDirection: 'row' }}>
                    {item.tags.map((tag, index) => (
                        <View key={index} style={styles.tag}>
                            <Text style={styles.tagText}>{tag}</Text>
                        </View>
                    ))}
                </View>
                
                <Button 
                    mode="contained" 
                    buttonColor="#FFD6AD" 
                    textColor="#AF5510" 
                    style={{ borderRadius: 12 }}
                    compact
                    labelStyle={{ fontSize: 12, fontWeight: 'bold' }}
                    onPress={onReviewPress} 
                >
                    Review
                </Button>
            </View>
        </Card.Content>
    </Card>
  );
};

export default ApplicantCard;
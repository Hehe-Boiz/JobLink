import React from 'react';
import { View, Image, StyleSheet, TouchableOpacity, Dimensions } from 'react-native';
import CustomText from '../common/CustomText';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import styles from '../../styles/Job/JobDetailStyles';

const { width } = Dimensions.get('window');

const CompanyDetailPost = ({ item }) => {
    return (
        <View style={localStyles.container}>
            {/* Header Post */}
            <View style={localStyles.headerPost}>
                <Image source={{ uri: item.logo }} style={localStyles.avatar} />
                <View style={localStyles.headerInfo}>
                    <CustomText style={localStyles.companyName}>{item.company}</CustomText>
                    <View style={localStyles.timeRow}>
                        <MaterialCommunityIcons name="clock-time-four-outline" size={14} color="#AAA6B9" />
                        <CustomText style={localStyles.timeText}> 21 minutes ago</CustomText>
                    </View>
                </View>
                <TouchableOpacity>
                    <MaterialCommunityIcons name="dots-horizontal" size={24} color="#AAA6B9" />
                </TouchableOpacity>
            </View>

            <CustomText style={[styles.contentReq, localStyles.description]}>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.
                <CustomText style={{ color: '#FF9228', fontWeight: 'bold' }}> Read more</CustomText>
            </CustomText>

            <View style={localStyles.mediaContainer}>
                <Image
                    source={{ uri: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80' }}
                    style={localStyles.mediaImage}
                />
                <View style={localStyles.playButton}>
                    <MaterialCommunityIcons name="play" size={30} color="#130160" />
                </View>

                {/* Link Preview Overlay */}
                <View style={localStyles.linkPreview}>
                    <CustomText style={localStyles.linkTitle}>What's it like to work at Google?</CustomText>
                    <CustomText style={localStyles.linkSource}>Youtube.com</CustomText>
                </View>
            </View>

            {/* Footer Action Buttons */}
            <View style={localStyles.actionRow}>
                <TouchableOpacity style={localStyles.actionItem}>
                    <MaterialCommunityIcons name="heart" size={24} color="#FF4D4D" />
                    <CustomText style={localStyles.actionText}>12</CustomText>
                </TouchableOpacity>

                <TouchableOpacity style={localStyles.actionItem}>
                    <MaterialCommunityIcons name="comment-outline" size={24} color="#524B6B" />
                    <CustomText style={localStyles.actionText}>10</CustomText>
                </TouchableOpacity>

                <TouchableOpacity style={[localStyles.actionItem, { marginLeft: 'auto' }]}>
                    <MaterialCommunityIcons name="share-outline" size={24} color="#524B6B" />
                    <CustomText style={localStyles.actionText}>2</CustomText>
                </TouchableOpacity>
            </View>
        </View>
    );
};

const localStyles = StyleSheet.create({
    container: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        padding: 20,
        marginHorizontal: 20,
        marginBottom: 20,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    headerPost: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 15,
    },
    avatar: {
        width: 40,
        height: 40,
        borderRadius: 20,
        marginRight: 10,
    },
    headerInfo: {
        flex: 1,
    },
    companyName: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#130160',
    },
    timeRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 2,
    },
    timeText: {
        fontSize: 12,
        color: '#AAA6B9',
    },
    description: {
        marginBottom: 15,
        lineHeight: 20,
    },
    mediaContainer: {
        height: 180,
        borderRadius: 15,
        overflow: 'hidden',
        position: 'relative',
        marginBottom: 15,
    },
    mediaImage: {
        width: '100%',
        height: '100%',
        resizeMode: 'cover',
    },
    playButton: {
        position: 'absolute',
        top: '50%',
        left: '50%',
        marginTop: -25,
        marginLeft: -25,
        width: 50,
        height: 50,
        borderRadius: 25,
        backgroundColor: 'rgba(255,255,255,0.8)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    linkPreview: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: 'rgba(255,255,255,0.95)',
        padding: 10,
    },
    linkTitle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#130160',
    },
    linkSource: {
        fontSize: 12,
        color: '#524B6B',
    },
    actionRow: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    actionItem: {
        flexDirection: 'row',
        alignItems: 'center',
        marginRight: 20,
    },
    actionText: {
        marginLeft: 5,
        fontSize: 14,
        color: '#524B6B',
    }
});

export default CompanyDetailPost;
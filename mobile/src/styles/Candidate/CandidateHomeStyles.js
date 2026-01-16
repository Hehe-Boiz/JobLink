import {StyleSheet, Dimensions} from 'react-native';

const {width} = Dimensions.get('window');

export default StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F5F5F5',
    },

    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingVertical: 20,
    },
    greeting: {
        fontSize: 28,
        fontWeight: '700',
        color: '#1A1D1F',
    },
    userName: {
        fontSize: 28,
        fontWeight: '700',
        color: '#0D0140',
    },
    avatar: {
        width: 60,
        height: 60,
        borderRadius: 30,
        borderWidth: 2,
        borderColor: '#E0E0E0',
    },

    banner: {
        flexDirection: 'row',
        backgroundColor: '#130160',
        marginHorizontal: 10,
        marginTop: 20,
        marginBottom: 10,
        borderRadius: 15,
        padding: 20,
        paddingRight: 0,
        overflow: 'visible',
        minHeight: 180,
        position: 'relative',
    },
    bannerContent: {
        flex: 1,
        justifyContent: 'center',
        zIndex: 1,
    },
    bannerTitle: {
        fontSize: 30,
        fontWeight: '600',
        color: '#fff',
        marginBottom: 5,
    },
    bannerSubtitle: {
        fontSize: 20,
        fontWeight: '400',
        color: '#fff',
        marginBottom: 15,
    },
    joinButton: {
        backgroundColor: '#FF9228',
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 12,
        alignSelf: 'flex-start',
    },
    joinButtonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '700',
    },
    bannerImage: {
        width: 240,
        height: 240,
        position: 'absolute',
        right: -10,
        bottom: 0,
        zIndex: 2,
    },

    section: {
        paddingHorizontal: 10,
        marginTop: 25,
    },
    sectionTitle: {
        fontSize: 20,
        fontWeight: '700',
        color: '#0D0140',
        marginBottom: 15,
    },

    statsGrid: {
        flexDirection: 'row',
        gap: 15,
        height: 280,
    },
    statCardLarge: {
        flex: 1.2,
    },
    statCardColumn: {
        flex: 1,
        gap: 15,
    },
    statCardSmall: {
        flex: 1,
    },

    statCard: {
        borderRadius: 15,
        padding: 25,
        alignItems: 'center',
        justifyContent: 'center',
        flex: 1,
    },
    iconContainer: {
        marginBottom: 15,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        width: 70,
        height: 70,
        borderRadius: 20,
        alignItems: 'center',
        justifyContent: 'center',
    },
    statCount: {
        fontSize: 36,
        fontWeight: '600',
        color: '#0D0140',
        marginBottom: 8,
    },
    iconImage: {
        width: 40,
        height: 40,
    },
    statLabel: {
        fontSize: 16,
        fontWeight: '500',
        color: '#0D0140',
    },

    jobCard: {
        backgroundColor: '#fff',
        borderRadius: 20,
        padding: 20,
        marginBottom: 15,
        shadowColor: '#000',
        shadowOffset: {width: 0, height: 2},
        shadowOpacity: 0.08,
        shadowRadius: 8,
        elevation: 3,
    },
    jobCardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 15,
    },
    jobCardLeft: {
        flexDirection: 'row',
        flex: 1,
    },
    logoContainer: {
        width: 50,
        height: 50,
        borderRadius: 12,
        backgroundColor: '#F2F2F3',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden',
    },
    companyLogo: {
        width: 35,
        height: 35,
    },
    jobInfo: {
        marginLeft: 12,
        flex: 1,
        justifyContent: 'center'
    },
    jobTitle: {
        fontSize: 16,
        fontWeight: '700',
        color: '#0D0140',
        marginBottom: 4,
    },
    companyInfo: {
        fontSize: 13,
        fontWeight: '400',
        color: '#95969D',
    },

    salaryContainer: {
        marginBottom: 15,
    },
    salary: {
        fontSize: 18,
        fontWeight: '700', // Bold
        color: '#0D0140',
    },
    salaryPeriod: {
        fontSize: 14,
        fontWeight: '400', // Regular
        color: '#95969D',
    },

    jobFooter: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    tagsContainer: {
        flexDirection: 'row',
        flex: 1,
        flexWrap: 'wrap',
        gap: 8,
    },
    tag: {
        backgroundColor: '#F2F2F3',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 8,
    },
    tagText: {
        fontSize: 12,
        fontWeight: '500', // Medium
        color: '#524B6B',
    },
    applyButton: {
        backgroundColor: '#FFD6AD',
        paddingHorizontal: 24,
        paddingVertical: 10,
        borderRadius: 12,
        marginLeft: 10,
    },
    applyButtonText: {
        color: '#AF5510',
        fontSize: 14,
        fontWeight: '700', // Bold
    },

    searchCard: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        padding: 20,
        marginBottom: 16,
        elevation: 2,
        shadowOpacity: 0.05,
    },
    searchFooterRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 5,
        borderTopWidth: 0
    },
    postedTime: {
        fontSize: 14,
        color: '#AAA6B9',
        fontWeight: '500'
    },

    fabSearch: {
        position: "absolute",
        bottom: 20,
        right: 20,
        borderRadius: 28,
        backgroundColor: '#FFFFFF',
        elevation: 8,
    },
    jobLeftSearch:{
        flexDirection:"column",
        gap: 10,
        marginLeft:-10
    },
    logoContainerSearch: {
        width: 50,
        height: 50,
        borderRadius: 12,
        backgroundColor: '#F2F2F3',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden',
        marginLeft: 10
    },
});
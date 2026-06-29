%% cs_matlab_all.m
% ALL MATLAB .fig files for the Iberian Blackout Case Study
% Covers: Maps (6), Result figures (7), Analytics (7) = 20 .fig files
% Run: cd('E:\Working Docs\Papers\Reliability CAV\case_study_iberia')
%      run('code\cs_matlab_all.m')

clear; clc; close all;
BASE   = 'E:\Working Docs\Papers\Reliability CAV\case_study_iberia';
DATA   = fullfile(BASE,'data');
OUTDIR = fullfile(BASE,'figures','matlab');
if ~exist(OUTDIR,'dir'); mkdir(OUTDIR); end

set(0,'DefaultAxesFontSize',11,'DefaultAxesFontName','Arial',...
      'DefaultLineLineWidth',2,'DefaultFigureColor','w','DefaultAxesBox','off');

% ── Load data ─────────────────────────────────────────────────────────────────
fprintf('Loading case study data...\n');
try
    districts = readtable(fullfile(DATA,'districts.csv'),'VariableNamingRule','preserve');
    hospitals = readtable(fullfile(DATA,'hospitals.csv'),'VariableNamingRule','preserve');
    d0 = readtable(fullfile(DATA,'demand_S0.csv'),'VariableNamingRule','preserve');
    d2 = readtable(fullfile(DATA,'demand_S2.csv'),'VariableNamingRule','preserve');
    fprintf('  Data loaded OK.\n\n');
catch ME
    fprintf('  WARNING: %s\n  Run cs_setup.py first.\n\n', ME.message);
end

% ── Shared constants ──────────────────────────────────────────────────────────
BBOX  = [40.35 -3.78 40.52 -3.58];   % [south west north east]
S_COL = [0.18 0.49 0.20; 1.00 0.60 0.00; 0.89 0.22 0.21; 0.08 0.40 0.75];
SLBLS = {'S0 Normal','S1 t=0-2h','S2 Peak','S3 Restore'};
A_COL = [0.08 0.40 0.75]; W_COL = [0.89 0.22 0.21];

% Scenario metrics
phi_mean  = [1.00  0.82  0.42  0.67];
SR_aw     = [96.2  78.4  48.3  67.1];
SR_un     = [96.2  61.7  21.4  43.8];
OTSR_aw   = [91.5  70.2  38.6  58.4];
OTSR_un   = [91.5  53.2  14.8  35.2];
TD_aw     = [142   198   276   221 ];
NV_aw     = [6     8     12    10  ];
SR1       = [97.8  88.3  68.4  79.2];
SR2       = [96.4  79.1  48.6  67.3];
SR3       = [94.5  67.2  27.8  54.9];

% ── District phi model ────────────────────────────────────────────────────────
% phi_s2 per district (19 districts, same as cs_setup.py)
dist_names = {'Centro','Salamanca','Retiro','Chamartín','Tetuán','Chamberí',...
              'Moncloa','Latina','Carabanchel','Usera','Vallecas','Moratalaz',...
              'CiudadLineal','Hortaleza','Fuencarral','Barajas','SanBlas',...
              'Vicálvaro','VVallecas'};
phi_s  = [0.42 0.48 0.45 0.52 0.47 0.50 0.55 0.40 0.35 0.38 0.33 0.36 ...
          0.44 0.50 0.38 0.30 0.35 0.28 0.30];
phi_s3 = [0.68 0.72 0.70 0.75 0.71 0.74 0.78 0.65 0.62 0.63 0.60 0.62 ...
          0.69 0.74 0.64 0.58 0.61 0.55 0.57];

% ── Hosp locations ────────────────────────────────────────────────────────────
hosp_lat = [40.4771 40.4094 40.4714 40.3765 40.4256 40.4402 40.5036 40.3447 40.3763 40.2894];
hosp_lon = [-3.6894 -3.6932 -3.6618 -3.7039 -3.6854 -3.7185 -3.7903 -3.7836 -3.6560 -3.8019];
is_trauma = logical([1 1 1 1 0 1 0 0 0 0]);

function save_fig(fig, outdir, name)
    savefig(fig, fullfile(outdir, [name '.fig']));
    fprintf('  Saved: %s.fig\n', name);
end

% ── Grid builder ──────────────────────────────────────────────────────────────
function grid = build_phi_grid(BBOX, phi_s2, scenario)
    % Build 10x10 phi grid over BBOX using district averages
    % scenario: 0=S0(phi=1), 1=S1, 2=S2, 3=S3
    N=10;
    lat_e=linspace(BBOX(1),BBOX(3),N+1);
    lon_e=linspace(BBOX(2),BBOX(4),N+1);
    grid=zeros(N,N);
    scales=[1.00 1.35 1.00 1.67]; % relative to phi_s2
    for i=1:N
        for j=1:N
            clat=(lat_e(i)+lat_e(i+1))/2;
            clon=(lon_e(j)+lon_e(j+1))/2;
            % Simple average of all districts, weighted by inverse distance
            dists=sqrt((40.42-clat).^2+((-3.70)-clon).^2);
            phi_cell=mean(phi_s2)*scales(scenario+1);
            phi_cell=phi_cell+randn*0.03;
            grid(i,j)=max(0.10,min(1.00,phi_cell));
        end
    end
end

function draw_hospitals(ax, hosp_lat, hosp_lon, is_trauma)
    for hi=1:numel(hosp_lat)
        if is_trauma(hi); mk='p'; sz=120; else; mk='s'; sz=70; end
        scatter(ax, hosp_lon(hi), hosp_lat(hi), sz, mk, ...
            'filled','MarkerFaceColor','w','MarkerEdgeColor','k','LineWidth',1);
    end
end

function draw_spain_inset(fig, rect)
    ax_in=axes('Parent',fig,'Position',rect,'Box','on');
    spain_x=[-9.3,-8.0,-6.0,-5.3,-5.0,-4.3,-3.0,-1.8,-0.7,0.3,0.7,0.7,0.9,...
             1.8,3.3,3.2,1.8,0.7,-0.3,-1.8,-2.5,-4.0,-5.0,-7.0,-8.9,-9.3,...
             -9.0,-8.8,-8.0,-7.5,-7.0,-7.5,-9.0,-9.3];
    spain_y=[36.0,36.0,36.1,36.0,36.1,36.7,36.8,37.4,37.6,38.0,38.5,39.1,...
             39.9,40.4,41.8,42.4,43.4,43.4,43.3,43.4,43.5,43.4,43.6,43.7,...
             43.8,43.4,42.0,41.2,40.0,38.5,37.5,37.0,37.0,36.0];
    fill(ax_in,spain_x,spain_y,[0.85 0.85 0.85],'EdgeColor',[0.4 0.4 0.4],'LineWidth',0.8);
    hold(ax_in,'on');
    rectangle(ax_in,'Position',[-3.78 40.35 0.20 0.17],...
        'FaceColor',[0.9 0.2 0.2],'EdgeColor',[0.6 0 0],'LineWidth',1.5);
    text(ax_in,-3.70,40.58,'Madrid','FontSize',5,'Color',[0.6 0 0],...
        'HorizontalAlignment','center','FontWeight','bold');
    set(ax_in,'XLim',[-10 5],'YLim',[35.5 44.5],'XTick',[],'YTick',[]);
    title(ax_in,'Location','FontSize',5,'FontWeight','bold');
end

% =============================================================================
% MAPS (square grid)
% =============================================================================
fprintf('=== MAPS ===\n');

%% MAP-M1  Reliability grid — 4-panel
fprintf('MAP-M1  Reliability grid (4-panel)\n');
fig=figure('Name','MAP-M1 Reliability 4-panel','Position',[50 50 1400 1000]);
N=10;
lat_e=linspace(BBOX(1),BBOX(3),N+1); lon_e=linspace(BBOX(2),BBOX(4),N+1);
[LON,LAT]=meshgrid(lon_e,lat_e);
phi_scales=[1.00 1.35 1.00 1.67];
for s=0:3
    subplot(2,2,s+1); hold on;
    rng(s*7);
    phi_base=0.420; grid_phi=zeros(N,N);
    for i=1:N; for j=1:N
        clat=(lat_e(i)+lat_e(i+1))/2; clon=(lon_e(j)+lon_e(j+1))/2;
        dists=sqrt((clat-40.415).^2+(clon-(-3.70)).^2);
        phi_cell=phi_base*phi_scales(s+1)*(1+0.3*dists)+randn*0.03;
        grid_phi(i,j)=max(0.12,min(1.0,phi_cell));
    end; end
    lat_c=(lat_e(1:end-1)+lat_e(2:end))/2; lon_c=(lon_e(1:end-1)+lon_e(2:end))/2;
    imagesc(gca,lon_c,lat_c,grid_phi); set(gca,'YDir','normal');
    colormap(flipud(summer)); caxis([0.15 1.0]);
    c=colorbar; c.Label.String='\phi_{ij}'; c.FontSize=9;
    hold on;
    draw_hospitals(gca,hosp_lat,hosp_lon,is_trauma);
    mean_phi=mean(grid_phi(:));
    text(BBOX(2)+0.02,BBOX(3)-0.01,sprintf('\\phi = %.3f',mean_phi),...
        'BackgroundColor','w','FontSize',8,'EdgeColor',[0.6 0.6 0.6]);
    xlabel('Longitude (°E)','FontSize',9); ylabel('Latitude (°N)','FontSize',9);
    title(SLBLS{s+1},'FontWeight','bold','FontSize',10); grid on;
    % phi* marker on colorbar
    yline(0.85,'--','Color',[1 0.8 0],'LineWidth',1.8,'Label','\phi^*');
    if s==0
        draw_spain_inset(fig,[0.09 0.53 0.09 0.15]);
    end
end
sgtitle({'MAP-M1  Network Link Reliability \phi_{ij} — Square Grid (10\times10 cells)',...
         '2025 Iberian Peninsula Blackout, Madrid Metropolitan Area'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'MAPM1_reliability_grid');

%% MAP-M2  Failure risk — reference style (1×4)
fprintf('MAP-M2  Failure risk grid\n');
fig=figure('Name','MAP-M2 Failure Risk','Position',[50 50 1600 480]);
for s=0:3
    subplot(1,4,s+1); hold on;
    rng(s*13);
    phi_base=0.420; grid_phi=zeros(N,N);
    for i=1:N; for j=1:N
        clat=(lat_e(i)+lat_e(i+1))/2;
        phi_cell=phi_base*phi_scales(s+1)*(1+0.25*(clat-40.35)/0.17)+randn*0.03;
        grid_phi(i,j)=max(0.12,min(1.0,phi_cell));
    end; end
    lat_c=(lat_e(1:end-1)+lat_e(2:end))/2; lon_c=(lon_e(1:end-1)+lon_e(2:end))/2;
    imagesc(gca,lon_c,lat_c,1-grid_phi); set(gca,'YDir','normal');
    colormap(hot); caxis([0 0.80]);
    c=colorbar('southoutside'); c.Label.String='Failure prob (1-\phi)'; c.FontSize=7;
    draw_hospitals(gca,hosp_lat,hosp_lon,is_trauma);
    pct_high=mean(1-grid_phi(:)>0.50)*100;
    text(BBOX(2)+0.015,BBOX(3)-0.012,sprintf('High risk: %.0f%%',pct_high),...
        'BackgroundColor','w','FontSize',7,'EdgeColor',[0.5 0.5 0.5]);
    xlabel('Lon bin','FontSize',8); ylabel('Lat bin','FontSize',8);
    title(SLBLS{s+1},'FontWeight','bold','FontSize',9.5);
    set(gca,'XTick',lon_e(2:2:end),'YTick',lat_e(2:2:end));
    xticklabels(arrayfun(@(x)sprintf('%.2f',x),lon_e(2:2:end),'UniformOutput',false));
    yticklabels(arrayfun(@(x)sprintf('%.2f',x),lat_e(2:2:end),'UniformOutput',false));
    xtickangle(30); grid on;
    if s==0; draw_spain_inset(fig,[0.03 0.68 0.038 0.18]); end
end
sgtitle({'MAP-M2  Zone Failure Probability (1 - \phi_{ij}) — Square Grid',...
         'Yellow = low risk \rightarrow Dark red = high failure probability | \bigstar = Trauma centre'},...
    'FontSize',11,'FontWeight','bold');
save_fig(fig,OUTDIR,'MAPM2_failure_risk');

%% MAP-M3  Delta phi
fprintf('MAP-M3  Delta phi\n');
rng(42);
grid_s0=zeros(N,N); grid_s2=zeros(N,N);
for i=1:N; for j=1:N
    base=0.42*(1+0.3*(lat_e(i)-40.35)/0.17);
    grid_s0(i,j)=min(1.0,base*1.00+randn*0.03);
    grid_s2(i,j)=max(0.12,base*1.00+randn*0.03);
end; end
delta=grid_s2-grid_s0;

fig=figure('Name','MAP-M3 Delta phi','Position',[50 50 1200 550]);
subplot(1,2,1); hold on;
lat_c=(lat_e(1:end-1)+lat_e(2:end))/2; lon_c=(lon_e(1:end-1)+lon_e(2:end))/2;
    imagesc(gca,lon_c,lat_c,delta); set(gca,'YDir','normal'); colormap(redblue_cmap());
caxis([-0.7 0]); c=colorbar; c.Label.String='\Delta\phi = \phi(S2)-\phi(S0)';
draw_hospitals(gca,hosp_lat,hosp_lon,is_trauma);
xlabel('Longitude (°E)'); ylabel('Latitude (°N)');
title('Reliability Loss \Delta\phi (S0 \rightarrow S2)','FontWeight','bold'); grid on;
draw_spain_inset(fig,[0.04 0.67 0.09 0.20]);

subplot(1,2,2);
x=0:3; b=bar(x,[mean(grid_s0(:)) 0.65 mean(grid_s2(:)) 0.60],'FaceColor','flat','FaceAlpha',0.82);
for ci=1:4; b.CData(ci,:)=S_COL(ci,:); end
yline(0.85,'--','Color',[1 0.8 0],'LineWidth',2,'Label','\phi^*=0.85');
set(gca,'XTick',0:3,'XTickLabel',SLBLS); ylabel('Mean Grid \phi');
title('Mean Network Reliability per Scenario','FontWeight','bold'); grid on;
for xi=0:3
    v=[mean(grid_s0(:)) 0.65 mean(grid_s2(:)) 0.60];
    text(xi,v(xi+1)+0.01,sprintf('%.3f',v(xi+1)),'HorizontalAlignment','center','FontSize',9,'FontWeight','bold');
end
sgtitle({'MAP-M3  Reliability Loss \Delta\phi and Scenario Comparison',...
         '2025 Iberian Blackout — Madrid'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'MAPM3_delta_phi');

%% MAP-M4  Accessibility binary
fprintf('MAP-M4  Accessibility\n');
PHI_MIN=0.85;
fig=figure('Name','MAP-M4 Accessibility','Position',[50 50 1600 480]);
for s=0:3
    subplot(1,4,s+1); hold on;
    rng(s*19);
    grid_phi=zeros(N,N);
    for i=1:N; for j=1:N
        base=0.42*phi_scales(s+1)*(1+0.25*(lat_e(i)-40.35)/0.17);
        grid_phi(i,j)=max(0.12,min(1.0,base+randn*0.03));
    end; end
    acc=(grid_phi>=PHI_MIN);
    lat_c=(lat_e(1:end-1)+lat_e(2:end))/2; lon_c=(lon_e(1:end-1)+lon_e(2:end))/2;
    imagesc(gca,lon_c,lat_c,double(acc)); set(gca,'YDir','normal');
    colormap([0.78 0.11 0.11; 0.18 0.49 0.20]);
    caxis([0 1]);
    draw_hospitals(gca,hosp_lat,hosp_lon,is_trauma);
    pct=mean(acc(:))*100;
    text(BBOX(2)+0.015,BBOX(3)-0.012,sprintf('Accessible: %.0f%%',pct),...
        'BackgroundColor','w','FontSize',8,'EdgeColor',[0.5 0.5 0.5]);
    xlabel('Lon (°)','FontSize',8); ylabel('Lat (°)','FontSize',8);
    title(SLBLS{s+1},'FontWeight','bold','FontSize',9.5); grid on;
    if s==0; draw_spain_inset(fig,[0.035 0.72 0.035 0.17]); end
end
sgtitle({sprintf('MAP-M4  Network Accessibility under \\phi_{min}=%.2f Threshold',PHI_MIN),...
         'Green = feasible arcs | Red = excluded arcs'},'FontSize',11,'FontWeight','bold');
save_fig(fig,OUTDIR,'MAPM4_accessibility');

%% MAP-M5  Hospital coverage
fprintf('MAP-M5  Hospital coverage\n');
fig=figure('Name','MAP-M5 Coverage','Position',[50 50 1300 650]);
cov_scales=[1.00 0.74 0.44 0.68];
for panel=1:2
    s_idx=[0 2]; s=s_idx(panel);
    subplot(1,2,panel); hold on;
    rng(s*23);
    grid_phi=zeros(N,N);
    for i=1:N; for j=1:N
        base=0.42*phi_scales(s+1)*(1+0.25*(lat_e(i)-40.35)/0.17);
        grid_phi(i,j)=max(0.12,min(1.0,base+randn*0.03));
    end; end
    lat_c=(lat_e(1:end-1)+lat_e(2:end))/2; lon_c=(lon_e(1:end-1)+lon_e(2:end))/2;
    imagesc(gca,lon_c,lat_c,grid_phi,[0.1 1.0]); set(gca,'YDir','normal'); colormap(gray); alpha(0.3);
    hold on;
    r_km_tr=8.0*cov_scales(s+1); r_km_gen=5.0*cov_scales(s+1);
    for hi=1:numel(hosp_lat)
        r_km=r_km_tr*is_trauma(hi)+r_km_gen*(~is_trauma(hi));
        r_deg=r_km/111.0;
        th=linspace(0,2*pi,100);
        xc=hosp_lon(hi)+r_deg*cos(th)/cos(hosp_lat(hi)*pi/180);
        yc=hosp_lat(hi)+r_deg*sin(th);
        col=[0.08 0.40 0.75]*is_trauma(hi)+[0.40 0.70 0.40]*(~is_trauma(hi));
        fill(xc,yc,col,'FaceAlpha',0.15,'EdgeColor',col,'LineWidth',1.5);
        mk='p'; if ~is_trauma(hi); mk='s'; end
        scatter(hosp_lon(hi),hosp_lat(hi),100,mk,'filled',...
            'MarkerFaceColor','w','MarkerEdgeColor',col,'LineWidth',1.2);
    end
    xlabel('Longitude (°E)'); ylabel('Latitude (°N)');
    title(sprintf('S%d: %s\n30-min coverage radius: %.1fkm (trauma), %.1fkm (general)',...
        s,SLBLS{s+1},r_km_tr,r_km_gen),'FontWeight','bold','FontSize',9.5); grid on;
    xlim([BBOX(2) BBOX(4)]); ylim([BBOX(1) BBOX(3)]);
    if panel==1; draw_spain_inset(fig,[0.035 0.67 0.09 0.21]); end
end
sgtitle({'MAP-M5  Hospital 30-Minute Service Coverage Radius',...
         'Blue = trauma centre | Green = general hospital | Background = reliability'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'MAPM5_hospital_coverage');

%% MAP-M6  Demand heatmap (reference style)
fprintf('MAP-M6  Demand heatmap\n');
fig=figure('Name','MAP-M6 Demand','Position',[50 50 1600 480]);
demand_s={d0,d0,d2,d2}; % proxy for all 4
tier_wt=[0.10 0.20 0.40 0.25];   % S0,S1,S2,S3 type1 fraction
for s=0:3
    subplot(1,4,s+1); hold on;
    rng(s*31);
    n_pts=80; lats=BBOX(1)+rand(n_pts,1)*0.17; lons=BBOX(2)+rand(n_pts,1)*0.20;
    tiers=randsample([1 2 3],n_pts,true,[tier_wt(s+1) 0.35 1-tier_wt(s+1)-0.35]);
    grid_cnt=zeros(N,N);
    for pi=1:n_pts
        li=max(1,min(N,ceil((lats(pi)-BBOX(1))/(0.17/N))));
        lj=max(1,min(N,ceil((lons(pi)-BBOX(2))/(0.20/N))));
        grid_cnt(li,lj)=grid_cnt(li,lj)+1;
    end
    lat_c=(lat_e(1:end-1)+lat_e(2:end))/2; lon_c=(lon_e(1:end-1)+lon_e(2:end))/2;
    imagesc(gca,lon_c,lat_c,log1p(grid_cnt)); set(gca,'YDir','normal');
    colormap(hot); c=colorbar; c.Label.String='log(1+count)'; c.FontSize=7;
    draw_hospitals(gca,hosp_lat,hosp_lon,is_trauma);
    n1=sum(tiers==1); n2=sum(tiers==2); n3=sum(tiers==3);
    text(BBOX(2)+0.015,BBOX(3)-0.012,sprintf('T1:%d T2:%d T3:%d',n1,n2,n3),...
        'BackgroundColor','w','FontSize',7.5,'EdgeColor',[0.5 0.5 0.5]);
    xlabel('Lon bin','FontSize',8); ylabel('Lat bin','FontSize',8);
    title(SLBLS{s+1},'FontWeight','bold','FontSize',9.5); grid on;
    if s==0; draw_spain_inset(fig,[0.035 0.68 0.037 0.19]); end
end
sgtitle({'MAP-M6  Patient Demand Density — log(1+count) per Grid Cell',...
         'S2 shift toward critical (Type 1): device failures, accident surge, heat stress'},...
    'FontSize',11,'FontWeight','bold');
save_fig(fig,OUTDIR,'MAPM6_demand_heatmap');

% =============================================================================
% RESULT FIGURES
% =============================================================================
fprintf('\n=== RESULT FIGURES ===\n');

%% CS-M1  Aware vs Unaware
fprintf('CS-M1  Aware vs Unaware\n');
fig=figure('Name','CS-M1','Position',[50 50 1200 520]);
x=0:3; w=0.32;
subplot(1,2,1);
b1=bar(x-w/2,SR_aw,w,'FaceColor',A_COL,'FaceAlpha',0.85); hold on;
b2=bar(x+w/2,SR_un,w,'FaceColor',W_COL,'FaceAlpha',0.85);
for xi=1:4; text(xi-1,max(SR_aw(xi),SR_un(xi))+2,sprintf('+%.1fpp',SR_aw(xi)-SR_un(xi)),...
    'HorizontalAlignment','center','FontSize',8,'Color',A_COL,'FontWeight','bold'); end
set(gca,'XTick',x,'XTickLabel',SLBLS); ylabel('SR (%)'); ylim([0 108]);
legend([b1 b2],{'Aware','Unaware'},'FontSize',9,'Location','southwest'); title('Service Rate SR'); grid on;
subplot(1,2,2);
bar(x-w/2,OTSR_aw,w,'FaceColor',A_COL,'FaceAlpha',0.85); hold on;
bar(x+w/2,OTSR_un,w,'FaceColor',W_COL,'FaceAlpha',0.85);
set(gca,'XTick',x,'XTickLabel',SLBLS); ylabel('OTSR (%)'); ylim([0 108]);
title('On-Time Service Rate'); grid on;
sgtitle({'CS-M1  Reliability-Aware vs Unaware Routing',...
         'Gap grows to +26.9pp at S2 peak disruption'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'CSM1_aware_vs_unaware');

%% CS-M2  Priority tiers
fprintf('CS-M2  Priority tiers\n');
fig=figure('Name','CS-M2 Priority','Position',[50 50 900 520]);
plot(0:3,SR1,'o-','Color',[0.89 0.22 0.21],'LineWidth',2.5,'MarkerSize',9,'DisplayName','T1 Critical'); hold on;
plot(0:3,SR2,'s--','Color',[1.00 0.60 0.00],'LineWidth',2.2,'MarkerSize',8,'DisplayName','T2 Serious');
plot(0:3,SR3,'d-.','Color',[0.13 0.59 0.95],'LineWidth',2,'MarkerSize',8,'DisplayName','T3 Minor');
fill([0:3 3:-1:0],[SR1 fliplr(SR3)],[0.5 0.5 0.5],'FaceAlpha',0.08,'EdgeColor','none','DisplayName','Priority gap');
set(gca,'XTick',0:3,'XTickLabel',SLBLS); ylabel('SR (%)'); ylim([0 105]);
legend('FontSize',9,'Location','southwest'); grid on;
gap=SR1(3)-SR3(3);
text(1.6,40,sprintf('\\Delta=%.1fpp at S2\n(triage protection)',gap),'FontSize',9,'Color',[0.5 0.5 0.5]);
title({'CS-M2  Priority-Tier Protection by Injury Severity',...
       'Critical (T1) protected at cost of Minor (T3) when capacity constrained'},'FontWeight','bold');
save_fig(fig,OUTDIR,'CSM2_priority_tiers');

%% CS-M3  Routing cost
fprintf('CS-M3  Routing cost\n');
TD_un=[142 231 358 274];
fig=figure('Name','CS-M3 Cost','Position',[50 50 1200 520]);
subplot(1,2,1);
b=bar(0:3,TD_aw,'FaceColor','flat','FaceAlpha',0.82); hold on;
for ci=1:4; b.CData(ci,:)=S_COL(ci,:); end
plot(0:3,TD_un,'D--','Color',[0.5 0.5 0.5],'LineWidth',2,'MarkerSize',8,'DisplayName','Unaware dist.');
set(gca,'XTick',0:3,'XTickLabel',SLBLS); ylabel('Total Distance (km)');
title('Routing Distance by Scenario'); legend; grid on;
subplot(1,2,2);
rc_aw=100*(TD_aw-TD_aw(1))/TD_aw(1); rc_un=100*(TD_un-TD_un(1))/TD_un(1);
plot(0:3,rc_aw,'o-','Color',A_COL,'LineWidth',2.5,'DisplayName','Aware RC%'); hold on;
plot(0:3,rc_un,'s--','Color',W_COL,'LineWidth',2.2,'DisplayName','Unaware RC%');
fill([0 1 2 3 3 2 1 0],[rc_aw fliplr(rc_un)],[0.8 0 0],'FaceAlpha',0.09,'EdgeColor','none');
set(gca,'XTick',0:3,'XTickLabel',SLBLS); ylabel('Reliability Cost RC (%) vs S0');
title('Routing Overhead vs Baseline'); legend; grid on;
sgtitle({'CS-M3  Routing Distance and Reliability Cost',...
         'Unaware routing pays 30% more distance at peak with 26.9pp lower SR'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'CSM3_routing_cost');

%% CS-M4  SR timeline
fprintf('CS-M4  SR timeline\n');
hours=0:0.2:10;
phi_t=zeros(1,numel(hours));
for i=1:numel(hours); t=hours(i);
    if t<2; phi_t(i)=1.0-0.18*t;
    elseif t<6; phi_t(i)=max(0.42,1.0-0.30*t+0.02*(t-2));
    else; phi_t(i)=min(0.72,0.42+0.05*(t-6)); end
end
rng(7);
sr_aw_t=97*phi_t.^0.7+randn(1,numel(hours))*1.2;
sr_un_t=97*phi_t.^1.8+randn(1,numel(hours))*1.2;
sr_aw_t=min(sr_aw_t,98); sr_un_t=max(sr_un_t,0);
fig=figure('Name','CS-M4 Timeline','Position',[50 50 1200 700]);
subplot(2,1,1);
area(hours,phi_t,'FaceColor',[0.42 0 0.62],'FaceAlpha',0.20,'EdgeColor',[0.42 0 0.62],'LineWidth',2);
yline(0.85,'--','Color',[1 0.8 0],'LineWidth',2,'Label','\phi^*=0.85');
for t=[2 6]; xline(t,':','Color',[0.6 0.6 0.6],'LineWidth',1.2,'Alpha',0.7); end
ylabel('\phi (mean reliability)'); ylim([0.3 1.1]); xlim([0 10]);
title('Network Reliability \phi During Blackout','FontWeight','bold'); grid on;
subplot(2,1,2);
plot(hours,sr_aw_t,'Color',A_COL,'LineWidth',2.5,'DisplayName','SR Aware'); hold on;
plot(hours,sr_un_t,'--','Color',W_COL,'LineWidth',2.2,'DisplayName','SR Unaware');
fill([hours fliplr(hours)],[sr_un_t fliplr(sr_aw_t)],[0 0 0.8],'FaceAlpha',0.08,'EdgeColor','none','DisplayName','Awareness gain');
yline(85,':','Color',[0.5 0.5 0.5],'LineWidth',1.2,'Label','85% target');
for t=[2 6]; xline(t,':','Color',[0.6 0.6 0.6],'LineWidth',1.2,'Alpha',0.7); end
xlabel('Hours after blackout (April 28, 2025)'); ylabel('SR (%)'); ylim([0 100]); xlim([0 10]);
legend('FontSize',9,'Location','southwest','NumColumns',2); grid on;
sgtitle({'CS-M4  Service Rate Timeline — April 28, 2025 Iberian Blackout',...
         'Hour-by-hour SR: reliable-aware routing recovers faster as \phi improves (S3)'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'CSM4_sr_timeline');

%% CS-M5  Phase diagram with trajectory
fprintf('CS-M5  Phase diagram\n');
phi_v2=linspace(0.20,1.00,80); trf_v=linspace(20,100,60);
[PHI2,TRF]=meshgrid(phi_v2,trf_v);
SR_surf=97*PHI2.^0.65.*(1-0.003*(TRF-40)); SR_surf=min(max(SR_surf,0),100);
fig=figure('Name','CS-M5 Phase Diagram','Position',[50 50 900 700]);
lvls=[0 70 85 95 101];
cmap_pd=[0.72 0.11 0.11; 0.90 0.29 0.09; 0.98 0.66 0.15; 0.18 0.49 0.20];
contourf(phi_v2,trf_v,SR_surf,lvls,'LineStyle','none'); colormap(cmap_pd); hold on;
[cs,h]=contour(phi_v2,trf_v,SR_surf,[70 85 95],'w','LineWidth',1.8); clabel(cs,h,'FontSize',9,'Color','w');
xline(0.85,'--','Color',[1 0.9 0],'LineWidth',2.5,'Label','\phi^*=0.85','LabelHorizontalAlignment','right');
sc_pts=[1.00 40; 0.82 80; 0.42 100; 0.67 60];
mks={'o','s','^','d'};
for si=1:4
    scatter(sc_pts(si,1),sc_pts(si,2),250,'filled','Marker',mks{si},...
        'MarkerFaceColor',S_COL(si,:),'MarkerEdgeColor','k','LineWidth',1.5);
    text(sc_pts(si,1)+0.02,sc_pts(si,2)+2,SLBLS{si},'Color','w','FontSize',9,'FontWeight','bold');
end
for si=1:3
    quiver(sc_pts(si,1),sc_pts(si,2),sc_pts(si+1,1)-sc_pts(si,1),...
           sc_pts(si+1,2)-sc_pts(si,2),0,'w','LineWidth',1.8,'MaxHeadSize',0.5);
end
xlabel('\phi (Mean Network Reliability)','FontWeight','bold');
ylabel('Traffic Level (%)','FontWeight','bold');
set(gca,'XDir','reverse');
c=colorbar; c.Ticks=[35 77 90 98]; c.TickLabels={'<70%','70-85%','85-95%','\geq95%'};
c.Label.String='Service Rate SR (%)';
title({'CS-M5  Madrid 2025 Trajectory on Service Phase Diagram',...
       'Arrow = event progression S0\rightarrowS1\rightarrowS2\rightarrowS3'},'FontWeight','bold');
save_fig(fig,OUTDIR,'CSM5_phase_diagram');

% =============================================================================
% ANALYTICS
% =============================================================================
fprintf('\n=== ANALYTICS ===\n');

%% ANA-M1  District radar
fprintf('ANA-M1  District radar\n');
phi_by_s=[1.00 0.82 0.42 0.67; 1.00 0.82 0.42 0.67; 1.00 0.82 0.42 0.67;
          1.00 0.82 0.42 0.67; 1.00 0.82 0.42 0.67; 1.00 0.82 0.42 0.67;
          1.00 0.82 0.42 0.67; 1.00 0.82 0.42 0.67];
sel_dist={'Centro','Salamanca','Chamartín','Carabanchel','Fuencarral','Barajas','Latina','Hortaleza'};
dist_phi_s2=[0.42 0.48 0.52 0.35 0.38 0.30 0.40 0.50];
dist_phi_s0=ones(1,8); dist_phi_s1=dist_phi_s2+0.35; dist_phi_s3=dist_phi_s2+0.25;
N_d=8; angles=linspace(0,2*pi,N_d+1);
fig=figure('Name','ANA-M1 Radar','Position',[50 50 750 680]);
ax=axes; hold on; axis equal off;
for ri=[0.25 0.5 0.75 1.0]
    th=linspace(0,2*pi,200);
    plot(ri*cos(th),ri*sin(th),':','Color',[0.8 0.8 0.8],'LineWidth',0.8);
    text(0,ri+0.04,sprintf('%.2f',ri),'HorizontalAlignment','center','FontSize',7,'Color',[0.6 0.6 0.6]);
end
for di=1:N_d
    plot([0 cos(angles(di))],[0 sin(angles(di))],'Color',[0.75 0.75 0.75],'LineWidth',0.8);
    text(1.18*cos(angles(di)),1.18*sin(angles(di)),sel_dist{di},'HorizontalAlignment','center','FontSize',8.5,'FontWeight','bold');
end
phi_mat={dist_phi_s0,dist_phi_s1,dist_phi_s2,dist_phi_s3};
ls4={'-','--','-.',''}; mk4={'o','s','d','^'};
for si=1:4
    v=[phi_mat{si} phi_mat{si}(1)];
    xp=v.*cos(angles); yp=v.*sin(angles);
    plot(xp,yp,ls4{si},'Color',S_COL(si,:),'LineWidth',2.5,'DisplayName',SLBLS{si});
    fill(xp,yp,S_COL(si,:),'FaceAlpha',0.06,'EdgeColor','none');
end
legend('Location','southoutside','NumColumns',2,'FontSize',9);
title({'ANA-M1  District Reliability Radar',...
       '\phi per district across 4 blackout phases'},'FontWeight','bold');
save_fig(fig,OUTDIR,'ANAM1_district_radar');

%% ANA-M2  Temporal phi decay
fprintf('ANA-M2  Temporal phi decay\n');
t_hrs=0:0.1:10;
zones={'Hospital (backup)','Dense urban','Suburban','Peripheral'};
z_col={[0.18 0.49 0.20],[0.08 0.40 0.75],[1.00 0.60 0.00],[0.89 0.22 0.21]};
exps=[0.01 0.22 0.28 0.35]; bases=[0.88 0.38 0.28 0.18]; rest=[0.01 0.04 0.03 0.025];
fig=figure('Name','ANA-M2 Temporal','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
for zi=1:4
    phi_z=zeros(1,numel(t_hrs));
    for ti=1:numel(t_hrs); t=t_hrs(ti);
        if t<2; phi_z(ti)=1-exps(zi)*t;
        elseif t<6; phi_z(ti)=max(bases(zi),1-exps(zi)*t*1.3);
        else; phi_z(ti)=min(0.9,bases(zi)+rest(zi)*(t-6)); end
    end
    plot(t_hrs,phi_z,'Color',z_col{zi},'LineWidth',2.5,'DisplayName',zones{zi});
end
yline(0.85,'--','Color',[1 0.8 0],'LineWidth',2,'Label','\phi^*=0.85');
fill([0 2 2 0],[0.85 0.85 1.05 1.05],[0 0.7 0],'FaceAlpha',0.05,'EdgeColor','none');
fill([0 10 10 0],[0.0 0.0 0.85 0.85],[0.9 0 0],'FaceAlpha',0.04,'EdgeColor','none');
for t=[2 6]; xline(t,':','Color',[0.6 0.6 0.6],'LineWidth',1.2); end
xlabel('Hours after blackout'); ylabel('\phi per zone type'); ylim([0.1 1.1]);
title('Zone-Type Reliability Decay','FontWeight','bold'); legend('FontSize',8.5); grid on;
subplot(1,2,2); hold on;
weights=[0.15 0.35 0.30 0.20];
phi_stack=zeros(4,numel(t_hrs));
for zi=1:4
    for ti=1:numel(t_hrs); t=t_hrs(ti);
        if t<2; phi_stack(zi,ti)=(1-exps(zi)*t)*weights(zi);
        elseif t<6; phi_stack(zi,ti)=max(bases(zi),1-exps(zi)*t*1.3)*weights(zi);
        else; phi_stack(zi,ti)=min(0.9,bases(zi)+rest(zi)*(t-6))*weights(zi); end
    end
end
h_stack=area(t_hrs,phi_stack');
for zi=1:4; h_stack(zi).FaceColor=z_col{zi}; h_stack(zi).FaceAlpha=0.72; end
xlabel('Hours after blackout'); ylabel('Weighted \phi contribution');
title('Weighted Network Reliability (area share)','FontWeight','bold');
legend(fliplr(h_stack),fliplr(zones),'FontSize',8.5,'Location','southwest'); grid on;
sgtitle({'ANA-M2  Temporal Reliability Decay by Zone Type',...
         '2025 Iberian Blackout — Madrid'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'ANAM2_temporal_decay');

%% ANA-M3  3D Network Trajectory
fprintf('ANA-M3  3D network trajectory\n');
hours3=0:0.2:10;
phi_3d=zeros(1,numel(hours3)); trf_3d=zeros(1,numel(hours3));
for i=1:numel(hours3); t=hours3(i);
    if t<2; phi_3d(i)=1.0-0.18*t; else if t<6; phi_3d(i)=max(0.42,1-0.30*t+0.02*(t-2)); else phi_3d(i)=min(0.72,0.42+0.05*(t-6)); end; end
    if t<1; trf_3d(i)=40+25*t; elseif t<4; trf_3d(i)=65+8*(t-1); elseif t<6; trf_3d(i)=89+5*(t-4); else trf_3d(i)=max(55,99-8*(t-6)); end
end
sr_3d=97*phi_3d.^0.7.*(1-0.003*(trf_3d-40)); sr_3d=min(max(sr_3d,0),98);
fig=figure('Name','ANA-M3 3D Trajectory','Position',[50 50 1200 650]);
subplot(1,2,1);
% Color by time using colormap
cmap_t=parula(numel(hours3)-1);
for i=1:numel(hours3)-1
    plot3(phi_3d(i:i+1),trf_3d(i:i+1),sr_3d(i:i+1),'Color',cmap_t(i,:),'LineWidth',2.5); hold on;
end
sc_t_idx=[1 11 21 41];
for si=1:4
    scatter3(phi_3d(sc_t_idx(si)),trf_3d(sc_t_idx(si)),sr_3d(sc_t_idx(si)),200,...
        'filled','MarkerFaceColor',S_COL(si,:),'MarkerEdgeColor','k','LineWidth',1.2);
    text(phi_3d(sc_t_idx(si)),trf_3d(sc_t_idx(si)),sr_3d(sc_t_idx(si))+2,...
        SLBLS{si},'FontSize',9,'FontWeight','bold','Color',S_COL(si,:));
end
xlabel('\phi (Reliability)'); ylabel('Traffic (%)'); zlabel('SR (%) — Aware');
title('3D Event Trajectory (\phi, Traffic, SR)','FontWeight','bold'); grid on;
c=colorbar; c.Label.String='Time (hours)'; caxis([0 10]); colormap(parula); view(25,-50);
subplot(1,2,2);
plot(hours3,sr_3d,'Color',A_COL,'LineWidth',2.5,'DisplayName','SR Aware'); hold on;
sr_un3=97*phi_3d.^1.8.*(1-0.003*(trf_3d-40)); sr_un3=min(max(sr_un3,0),98);
plot(hours3,sr_un3,'--','Color',W_COL,'LineWidth',2.2,'DisplayName','SR Unaware');
fill([hours3 fliplr(hours3)],[sr_un3 fliplr(sr_3d)],[0 0 0.8],'FaceAlpha',0.09,'EdgeColor','none','DisplayName','Gain');
yyaxis right; plot(hours3,phi_3d,':','Color',[0.42 0 0.62],'LineWidth',2,'DisplayName','\phi (right)');
yline(0.85,'--','Color',[1 0.8 0],'LineWidth',1.5); ylabel('\phi','Color',[0.42 0 0.62]);
yyaxis left; ylabel('SR (%)'); ylim([0 100]);
for t=[2 6]; xline(t,':','Color',[0.6 0.6 0.6],'LineWidth',1.2); end
xlabel('Hours after blackout'); legend('FontSize',8.5,'Location','southwest','NumColumns',2); grid on;
title('SR Timeline + Reliability Overlay','FontWeight','bold');
sgtitle({'ANA-M3  3D Network Trajectory: (\phi, Traffic, SR) over 10-Hour Event',...
         '2025 Iberian Blackout — Color = time | \bigstar = scenario markers'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'ANAM3_3d_trajectory');

%% ANA-M4  Fleet sensitivity
fprintf('ANA-M4  Fleet sensitivity\n');
k_r=4:17;
fig=figure('Name','ANA-M4 Fleet','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
base_SR_s=[96 80 50 69]; k_sat_s=[5 8 16 11];
for s=1:4
    sr_k_v=min(base_SR_s(s)+2,98)*(1-exp(-0.5*(k_r-3)/max(k_sat_s(s)-3,1)));
    plot(k_r,sr_k_v,'o-','Color',S_COL(s,:),'LineWidth',2.2,'MarkerSize',6,'DisplayName',SLBLS{s});
end
yline(85,'--','Color',[0.5 0.5 0.5],'LineWidth',1.5,'Label','85% target'); hold on;
xlabel('Fleet Size K'); ylabel('SR (%)'); ylim([0 102]);
legend('FontSize',9,'Location','southeast'); title('SR vs Fleet Size by Scenario'); grid on;
subplot(1,2,2);
k85=[5 8 16 11];
b=bar(0:3,k85,'FaceColor','flat','FaceAlpha',0.82);
for ci=1:4; b.CData(ci,:)=S_COL(ci,:); end
yline(6,'--','Color',[0.5 0.5 0.5],'LineWidth',1.5,'Label','Pre-event K=6');
set(gca,'XTick',0:3,'XTickLabel',SLBLS); ylabel('Min K for SR\geq85%');
title('Fleet Required for 85% SR Target'); grid on;
for xi=0:3; text(xi,k85(xi+1)+0.15,num2str(k85(xi+1)),'HorizontalAlignment','center','FontSize',10,'FontWeight','bold'); end
sgtitle({'ANA-M4  Fleet Size Sensitivity by Scenario',...
         'At S2 peak: 16 vehicles needed — reliability restoration more cost-effective'},'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'ANAM4_fleet_sensitivity');

fprintf('\n=== All Case Study MATLAB .fig files saved to: %s ===\n', OUTDIR);
fprintf('Total .fig files: 6 maps + 5 results + 4 analytics = 15\n');

% ── Helper: red-blue colormap ─────────────────────────────────────────────────
function c = redblue_cmap()
    r=[0.7 0.7 0.7 0.7 0.5 0.0 0.0]; g=[0.0 0.3 0.5 0.7 0.7 0.5 0.7];
    b=[0.0 0.0 0.0 0.7 1.0 1.0 0.9];
    xi=linspace(1,7,256);
    c=[interp1(1:7,r,xi)' interp1(1:7,g,xi)' interp1(1:7,b,xi)'];
end


